"""Project 6.2: train the mini-GPT on Shakespeare (character level).

python train.py            # ~10M chars seen, ~15-30 min on CPU, ~3 min on a GPU -> ckpt.pt
python train.py --smoke    # a few seconds
"""
import os
import sys
import time
import urllib.request

import torch

from model import GPT, Config

SMOKE = "--smoke" in sys.argv
URL = "https://raw.githubusercontent.com/karpathy/char-rnn/master/data/tinyshakespeare/input.txt"
device = "cuda" if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else "cpu"
torch.manual_seed(1337)

if not os.path.exists("input.txt"):
    urllib.request.urlretrieve(URL, "input.txt")
text = open("input.txt", encoding="utf-8").read()
chars = sorted(set(text))
stoi, itos = {c: i for i, c in enumerate(chars)}, {i: c for i, c in enumerate(chars)}
encode = lambda s: [stoi[c] for c in s]
decode = lambda ids: "".join(itos[i] for i in ids)

data = torch.tensor(encode(text))
n = int(0.9 * len(data))
train_data, val_data = data[:n], data[n:]          # last 10% kept for honest evaluation

cfg = Config(vocab_size=len(chars), **({"n_layer": 2, "n_embd": 64, "n_head": 4, "block_size": 32} if SMOKE else {}))
max_iters, batch_size, eval_every = (30, 8, 10) if SMOKE else (3000, 32, 300)
model = GPT(cfg).to(device)
optimizer = torch.optim.AdamW(model.parameters(), lr=1e-3)
print(f"{len(text):,} characters | vocab {len(chars)} | {sum(p.numel() for p in model.parameters()) / 1e6:.2f}M parameters | {device}")


def get_batch(split):
    d = train_data if split == "train" else val_data
    ix = torch.randint(len(d) - cfg.block_size, (batch_size,))
    x = torch.stack([d[i:i + cfg.block_size] for i in ix])
    y = torch.stack([d[i + 1:i + cfg.block_size + 1] for i in ix])   # targets = inputs shifted by one
    return x.to(device), y.to(device)


@torch.no_grad()
def estimate_loss():
    model.eval()
    out = {s: torch.stack([model(*get_batch(s))[1] for _ in range(20)]).mean().item() for s in ("train", "val")}
    model.train()
    return out


t0 = time.time()
for it in range(max_iters + 1):
    if it % eval_every == 0:
        losses = estimate_loss()
        print(f"iter {it:5d} | train {losses['train']:.3f} | val {losses['val']:.3f} | {time.time() - t0:.0f}s")
    _, loss = model(*get_batch("train"))
    optimizer.zero_grad(set_to_none=True)
    loss.backward()
    torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
    optimizer.step()

torch.save({"model": model.state_dict(), "config": cfg.__dict__, "chars": chars}, "ckpt.pt")
start = torch.tensor([encode("ROMEO:\n")], device=device)
print("\n" + decode(model.generate(start, 300 if not SMOKE else 50)[0].tolist()))
