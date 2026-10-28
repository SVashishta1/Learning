"""Lesson 14: train the GPT from gpt.py on Shakespeare, one character at a time.

python train.py                 # CPU-friendly default: ~0.8M parameters, 2,000 steps, a few minutes
python train.py --steps 300     # a quick look
python train.py --size video    # the 10.8M-parameter model from Karpathy's video (use a GPU)
Saves the trained model to ckpt.pt (used by generate.py and lesson 16).
"""
import argparse
import os
import time
import urllib.request

import torch

from gpt import GPT, GPTConfig

URL = "https://raw.githubusercontent.com/karpathy/char-rnn/master/data/tinyshakespeare/input.txt"
SIZES = {   # model shape + training settings
    "tiny":  dict(n_layer=4, n_head=4, n_embd=128, block_size=64, dropout=0.0, batch_size=32, lr=1e-3, steps=2000),
    "video": dict(n_layer=6, n_head=6, n_embd=384, block_size=256, dropout=0.2, batch_size=64, lr=3e-4, steps=5000),
}
parser = argparse.ArgumentParser()
parser.add_argument("--size", choices=SIZES, default="tiny")
parser.add_argument("--steps", type=int, help="training steps (default depends on --size)")
parser.add_argument("--eval-every", type=int, default=250)
parser.add_argument("--device", default="cuda" if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else "cpu")
args = parser.parse_args()
S = SIZES[args.size]
steps = args.steps or S["steps"]
torch.manual_seed(1337)

# ---------------------------------------------------------------- data: text -> integers
if not os.path.exists("input.txt"):
    print("downloading tinyshakespeare (1 MB)...")
    urllib.request.urlretrieve(URL, "input.txt")
text = open("input.txt", encoding="utf-8").read()
chars = sorted(set(text))                                  # the vocabulary: every distinct character
stoi = {ch: i for i, ch in enumerate(chars)}               # string -> integer
itos = {i: ch for i, ch in enumerate(chars)}               # integer -> string
encode = lambda s: [stoi[c] for c in s]
decode = lambda ids: "".join(itos[i] for i in ids)

data = torch.tensor(encode(text), dtype=torch.long)
n = int(0.9 * len(data))
train_data, val_data = data[:n], data[n:]                  # the model never trains on the last 10%

cfg = GPTConfig(vocab_size=len(chars), n_layer=S["n_layer"], n_head=S["n_head"],
                n_embd=S["n_embd"], block_size=S["block_size"], dropout=S["dropout"])
model = GPT(cfg).to(args.device)
optimizer = torch.optim.AdamW(model.parameters(), lr=S["lr"])
print(f"{len(text):,} characters | vocab {len(chars)} | {model.num_params() / 1e6:.2f}M parameters | "
      f"device {args.device} | {steps} steps")


def get_batch(split):
    """batch_size random windows of block_size characters; targets = the same windows shifted by one."""
    d = train_data if split == "train" else val_data
    ix = torch.randint(len(d) - cfg.block_size, (S["batch_size"],))
    x = torch.stack([d[i:i + cfg.block_size] for i in ix])
    y = torch.stack([d[i + 1:i + cfg.block_size + 1] for i in ix])
    return x.to(args.device), y.to(args.device)


@torch.no_grad()
def estimate_loss(iters=20):
    """Average loss over a few batches, with dropout off: a calmer number than one batch."""
    model.eval()
    out = {}
    for split in ("train", "val"):
        out[split] = torch.stack([model(*get_batch(split))[1] for _ in range(iters)]).mean().item()
    model.train()
    return out


def sample(n_chars=150):
    start = torch.tensor([encode("\n")], device=args.device)
    model.eval()
    out = decode(model.generate(start, n_chars, temperature=0.8, top_k=None)[0].tolist())
    model.train()
    return out.strip()


t0 = time.time()
for step in range(steps + 1):
    if step % args.eval_every == 0 or step == steps:
        losses = estimate_loss()
        print(f"\nstep {step:5d} | train loss {losses['train']:.3f} | val loss {losses['val']:.3f} | {time.time() - t0:.0f}s")
        if step % (2 * args.eval_every) == 0 or step == steps:
            print("--- sample ---\n" + sample() + "\n--------------")
    if step == steps:
        break
    xb, yb = get_batch("train")
    _, loss = model(xb, yb)                          # 1. forward: how wrong are we?
    optimizer.zero_grad(set_to_none=True)            # 2. forget the previous step's gradients
    loss.backward()                                  # 3. backprop: which way should each weight move?
    optimizer.step()                                 # 4. move every weight a little bit

torch.save({"model": model.state_dict(), "config": cfg.__dict__, "chars": chars}, "ckpt.pt")
print(f"\nsaved ckpt.pt after {time.time() - t0:.0f}s")
