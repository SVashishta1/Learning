"""Project 5.3: a tiny character-level RNN (GRU) that generates names.
Unlike the bigram model, it carries a 'memory' (hidden state) of ALL the letters so far.

python rnn_names.py           # ~2-4 minutes on CPU
python rnn_names.py --smoke   # quick wiring check
"""
import sys

import torch
from torch import nn

from get_names import load_names

SMOKE = "--smoke" in sys.argv
torch.manual_seed(42)
names = load_names()[:500] if SMOKE else load_names()
chars = ["."] + sorted(set("".join(names)))           # "." = start/end token
stoi = {c: i for i, c in enumerate(chars)}
V = len(chars)


class NameRNN(nn.Module):
    def __init__(self, vocab, emb=24, hidden=128):
        super().__init__()
        self.embed = nn.Embedding(vocab, emb)             # each letter -> a small learned vector
        self.rnn = nn.GRU(emb, hidden, batch_first=True)  # reads letters one by one, updating its memory
        self.head = nn.Linear(hidden, vocab)              # memory -> scores for the next letter

    def forward(self, x, h=None):
        out, h = self.rnn(self.embed(x), h)
        return self.head(out), h


def make_batch(batch_names):
    """'emma' -> input '.emma', target 'emma.' (predict the next letter at every position). Pad to equal length."""
    seqs = [[0] + [stoi[c] for c in n] + [0] for n in batch_names]
    L = max(len(s) for s in seqs)
    x = torch.full((len(seqs), L - 1), 0)
    y = torch.full((len(seqs), L - 1), -100)              # -100 = "ignore this position" in the loss
    for i, s in enumerate(seqs):
        x[i, :len(s) - 1] = torch.tensor(s[:-1])
        y[i, :len(s) - 1] = torch.tensor(s[1:])
    return x, y


@torch.no_grad()
def sample(model, temperature=0.8, max_len=20):
    x, h, out = torch.tensor([[0]]), None, []
    for _ in range(max_len):
        logits, h = model(x, h)
        probs = torch.softmax(logits[0, -1] / temperature, dim=0)   # temperature < 1 = safer, > 1 = wilder
        ix = torch.multinomial(probs, 1).item()
        if ix == 0:
            break
        out.append(chars[ix])
        x = torch.tensor([[ix]])
    return "".join(out)


@torch.no_grad()
def full_loss(model):
    """Average loss over EVERY name (not just one random batch), so you can compare it with the bigram's 2.455."""
    total, count = 0.0, 0
    for i in range(0, len(names), 1000):
        x, y = make_batch(names[i:i + 1000])
        logits, _ = model(x)
        total += nn.functional.cross_entropy(logits.reshape(-1, V), y.reshape(-1), ignore_index=-100, reduction="sum").item()
        count += (y != -100).sum().item()          # number of real (non-padding) letters
    return total / count


model = NameRNN(V)
opt = torch.optim.Adam(model.parameters(), lr=3e-3)
loss_fn = nn.CrossEntropyLoss(ignore_index=-100)
steps = 50 if SMOKE else 3000
for step in range(1, steps + 1):
    batch = [names[i] for i in torch.randint(0, len(names), (64,))]   # 64 random names
    x, y = make_batch(batch)
    logits, _ = model(x)                                  # scores for the next letter at every position
    loss = loss_fn(logits.reshape(-1, V), y.reshape(-1))
    opt.zero_grad(); loss.backward()
    nn.utils.clip_grad_norm_(model.parameters(), 1.0)     # RNNs can have exploding gradients; clip them
    opt.step()
    if step % (steps // 6) == 0:
        print(f"step {step:5d} | loss {loss.item():.3f} | sample: {sample(model)}")

print(f"\nloss on all {len(names)} names: {full_loss(model):.3f}  (the bigram model in 5.2 got 2.455)")
print("\nFresh names (temperature 0.8):", ", ".join(sample(model) for _ in range(10)))
print("Wild names   (temperature 1.5):", ", ".join(sample(model, 1.5) for _ in range(5)))
in_data = set(names)
new = [n for n in (sample(model) for _ in range(200)) if n and n not in in_data]
print(f"{len(new)}/200 samples are brand-new names not in the dataset, e.g. {new[:6]}")
