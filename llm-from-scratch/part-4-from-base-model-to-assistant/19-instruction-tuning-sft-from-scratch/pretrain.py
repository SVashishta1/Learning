"""Lesson 19, step 1: make a BASE model. A LLaMA-style GPT (lesson 17) trained on Shakespeare,
with a vocabulary that already reserves the 3 chat special tokens (they just never appear yet).

python pretrain.py               # 2,000 steps, ~5-15 min on a laptop CPU -> base.pt
python pretrain.py --steps 500   # quicker, weaker base model
"""
import argparse
import time

import torch

from common import DEVICE, load_shakespeare, save_model, tok
from model import GPT, Config, LLAMA_STYLE

p = argparse.ArgumentParser()
p.add_argument("--steps", type=int, default=2000)
args = p.parse_args()
torch.manual_seed(1337)

text = load_shakespeare()
data = torch.tensor(tok.encode(text), dtype=torch.long)
n = int(0.9 * len(data))
train_data, val_data = data[:n], data[n:]                 # lesson 21 measures perplexity on this same val part
cfg = Config(vocab_size=tok.vocab_size, block_size=96, n_layer=4, n_head=4, n_embd=128, **LLAMA_STYLE)
model = GPT(cfg).to(DEVICE)
opt = torch.optim.AdamW(model.parameters(), lr=1e-3, weight_decay=0.1)
print(f"base model: {model.num_params():,} parameters | vocab {tok.vocab_size} (96 characters + 3 special tokens) | {DEVICE}")


def batch(d, B=32):
    ix = torch.randint(len(d) - cfg.block_size - 1, (B,))
    x = torch.stack([d[i:i + cfg.block_size] for i in ix])
    y = torch.stack([d[i + 1:i + cfg.block_size + 1] for i in ix])
    return x.to(DEVICE), y.to(DEVICE)


t0 = time.time()
for step in range(args.steps + 1):
    if step % 500 == 0 or step == args.steps:
        model.eval()
        with torch.no_grad():
            val = torch.stack([model(*batch(val_data))[1] for _ in range(10)]).mean().item()
        model.train()
        print(f"step {step:5d} | val loss {val:.3f} | {time.time() - t0:.0f}s")
    if step == args.steps:
        break
    _, loss = model(*batch(train_data))
    opt.zero_grad(set_to_none=True)
    loss.backward()
    torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
    opt.step()

save_model(model, "base.pt")
start = torch.tensor([tok.encode("ROMEO:\n")], device=DEVICE)
print("saved base.pt\n--- sample ---\n" + tok.decode(model.eval().generate(start, 150)[0].tolist()))
