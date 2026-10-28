"""Lesson 17, part 2: train lesson 14's GPT-2-style model and the LLaMA-style model on the SAME data,
with the SAME seed, steps and batch size, and compare their validation loss.

python compare.py                  # 2 models x 1,000 steps (~5-10 min on a laptop CPU)
python compare.py --ablation       # also swap ONE idea at a time (4 more runs)
python compare.py --steps 300      # quicker, noisier
"""
import argparse
import os
import time
import urllib.request

import torch

from model import GPT, Config, GPT2_STYLE, LLAMA_STYLE

URL = "https://raw.githubusercontent.com/karpathy/char-rnn/master/data/tinyshakespeare/input.txt"
p = argparse.ArgumentParser()
p.add_argument("--steps", type=int, default=1000)
p.add_argument("--eval-every", type=int, default=250)
p.add_argument("--ablation", action="store_true")
args = p.parse_args()
device = "cuda" if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else "cpu"

if not os.path.exists("input.txt"):
    urllib.request.urlretrieve(URL, "input.txt")
text = open("input.txt", encoding="utf-8").read()
chars = sorted(set(text))
stoi = {c: i for i, c in enumerate(chars)}
data = torch.tensor([stoi[c] for c in text])
n = int(0.9 * len(data))
train_data, val_data = data[:n], data[n:]
BLOCK, BATCH = 64, 32


def get_batch(d, gen):
    ix = torch.randint(len(d) - BLOCK, (BATCH,), generator=gen)       # gen: every model sees the same batches
    x = torch.stack([d[i:i + BLOCK] for i in ix])
    y = torch.stack([d[i + 1:i + BLOCK + 1] for i in ix])
    return x.to(device), y.to(device)


@torch.no_grad()
def val_loss(model):
    model.eval()
    gen = torch.Generator().manual_seed(999)                          # the same 20 validation batches every time
    loss = torch.stack([model(*get_batch(val_data, gen))[1] for _ in range(20)]).mean().item()
    model.train()
    return loss


def run(name, style):
    torch.manual_seed(1337)
    model = GPT(Config(vocab_size=len(chars), block_size=BLOCK, **style)).to(device)
    opt = torch.optim.AdamW(model.parameters(), lr=1e-3)
    gen = torch.Generator().manual_seed(1337)
    history, t0 = [], time.time()
    for step in range(args.steps + 1):
        if step % args.eval_every == 0 or step == args.steps:
            history.append(val_loss(model))
        if step == args.steps:
            break
        _, loss = model(*get_batch(train_data, gen))
        opt.zero_grad(set_to_none=True)
        loss.backward()
        opt.step()
    secs = time.time() - t0
    print(f"{name:28s} {model.num_params():>9,} " + "".join(f"{v:8.3f}" for v in history) + f"   {secs:5.0f}s")
    return history[-1]


runs = [("GPT-2 style (lesson 14)", GPT2_STYLE), ("LLaMA style", LLAMA_STYLE)]
if args.ablation:   # start from GPT-2 style and change exactly one thing
    runs += [("GPT-2 + RMSNorm", {**GPT2_STYLE, "norm": "rmsnorm"}),
             ("GPT-2 + RoPE", {**GPT2_STYLE, "pos": "rope"}),
             ("GPT-2 + SwiGLU", {**GPT2_STYLE, "mlp": "swiglu"}),
             ("GPT-2 + GQA (2 kv heads)", {**GPT2_STYLE, "n_kv_head": 2})]
evals = list(range(0, args.steps, args.eval_every)) + [args.steps]
print(f"device {device} | {args.steps} steps | batch {BATCH} x {BLOCK} characters | validation loss at steps:")
print(f"{'model':28s} {'params':>9s} " + "".join(f"{s:8d}" for s in evals) + "    time")
results = {name: run(name, style) for name, style in runs}
best = min(results, key=results.get)
print(f"\nlowest final validation loss: {best} ({results[best]:.3f})")
