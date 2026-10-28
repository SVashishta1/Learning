"""Capstone stage 3: pretrain the base model (LLaMA-style GPT from lesson 17) on your tokens.

python pretrain.py                  # CPU default: ~1M parameters, 2,000 steps (~10-20 min)
python pretrain.py --depth 8 --width 384 --steps 5000 --batch 64     # a GPU-sized run (see README)
-> base.pt
"""
import argparse
import math
import time

import numpy as np
import torch

from common import DEVICE, load_tokenizer, save_model
from model import GPT, Config, LLAMA_STYLE

p = argparse.ArgumentParser()
p.add_argument("--depth", type=int, default=4, help="number of transformer blocks")
p.add_argument("--width", type=int, default=128, help="n_embd; heads = width // 32")
p.add_argument("--context", type=int, default=128, help="block_size in tokens")
p.add_argument("--steps", type=int, default=2000)
p.add_argument("--batch", type=int, default=32)
p.add_argument("--lr", type=float, default=2e-3)
args = p.parse_args()
torch.manual_seed(1337)

tok = load_tokenizer()
train = torch.from_numpy(np.load("data/train.npy").astype(np.int64))
val = torch.from_numpy(np.load("data/val.npy").astype(np.int64))
n_head = max(1, args.width // 32)
cfg = Config(vocab_size=tok.vocab_size, block_size=args.context, n_layer=args.depth, n_head=n_head,
             n_embd=args.width, **{**LLAMA_STYLE, "n_kv_head": max(1, n_head // 2)})
model = GPT(cfg).to(DEVICE)
opt = torch.optim.AdamW(model.parameters(), lr=args.lr, betas=(0.9, 0.95), weight_decay=0.1)
print(f"{model.num_params():,} parameters | {len(train):,} training tokens | {args.steps} steps x "
      f"{args.batch * args.context:,} tokens | {DEVICE}")


def batch(d):
    ix = torch.randint(len(d) - cfg.block_size - 1, (args.batch,))
    x = torch.stack([d[i:i + cfg.block_size] for i in ix])
    y = torch.stack([d[i + 1:i + cfg.block_size + 1] for i in ix])
    return x.to(DEVICE), y.to(DEVICE)


def lr_at(step):                                     # warm-up, then cosine down to 10% (lesson 15)
    warm = max(1, args.steps // 20)
    if step < warm:
        return args.lr * (step + 1) / warm
    return args.lr * (0.1 + 0.45 * (1 + math.cos(math.pi * (step - warm) / max(1, args.steps - warm))))


t0 = time.time()
for step in range(args.steps + 1):
    if step % 250 == 0 or step == args.steps:
        model.eval()
        with torch.no_grad():
            v = torch.stack([model(*batch(val))[1] for _ in range(10)]).mean().item()
        model.train()
        print(f"step {step:5d} | val loss {v:.3f} | lr {lr_at(step):.1e} | {time.time() - t0:.0f}s")
    if step == args.steps:
        break
    for g in opt.param_groups:
        g["lr"] = lr_at(step)
    _, loss = model(*batch(train))
    opt.zero_grad(set_to_none=True)
    loss.backward()
    torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
    opt.step()

save_model(model, "base.pt")
start = torch.tensor([[tok.special_tokens["<|endoftext|>"]]], device=DEVICE)
sample = model.eval().generate(start, 80, temperature=0.8, top_k=40)[0].tolist()[1:]
print("saved base.pt\n--- the base model writes ---\n" + tok.decode(sample))
