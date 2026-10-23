"""Lesson 16, part 1: how a model picks the next token. Greedy, temperature, top-k, top-p, with text bar charts.

python sampling.py                                   # uses lesson 14's trained model if it exists
python sampling.py --ckpt path/to/ckpt.pt
"""
import argparse
import os

import torch
from torch.nn import functional as F

from model import GPT, GPTConfig, filter_logits

p = argparse.ArgumentParser()
p.add_argument("--ckpt", default="../14-build-gpt-from-scratch/ckpt.pt")
args = p.parse_args()


def bars(probs, labels, width=40):
    """Draw probabilities as a horizontal bar chart made of █ characters."""
    for lab, pr in zip(labels, probs):
        print(f"  {lab:>8s} {pr:6.1%} " + "█" * round(float(pr) * width))


# ----------------------------------------------------------------------------- 1. a toy example
print("=" * 70 + "\n1) Toy example: the model's scores for the word after 'The cat sat on the'\n" + "=" * 70)
words = ["mat", "sofa", "floor", "bed", "roof", "moon", "banana"]
logits = torch.tensor([[3.0, 2.2, 2.0, 1.5, 0.5, -0.5, -1.5]])   # raw scores (logits) from the model
print("raw scores (logits):", logits[0].tolist())

print("\ngreedy = always the highest score -> always 'mat' (same text every time)")
for t in (0.5, 1.0, 2.0):
    print(f"\ntemperature {t}: probabilities = softmax(scores / {t})")
    bars(F.softmax(filter_logits(logits, temperature=t), dim=-1)[0], words)
print("\ntop-k = 3: keep the 3 best, set the rest to 0, re-normalise")
bars(F.softmax(filter_logits(logits, top_k=3), dim=-1)[0], words)
print("\ntop-p = 0.9: keep the smallest set of best words whose probabilities add up to at least 90%")
bars(F.softmax(filter_logits(logits, top_p=0.9), dim=-1)[0], words)

# ----------------------------------------------------------------------------- 2. the real model
print("\n" + "=" * 70 + "\n2) Lesson 14's Shakespeare model\n" + "=" * 70)
if not os.path.exists(args.ckpt):
    raise SystemExit(f"No checkpoint at {args.ckpt}. Run lesson 14 first:  cd ../14-build-gpt-from-scratch && python train.py")
ckpt = torch.load(args.ckpt, map_location="cpu")
model = GPT(GPTConfig(**ckpt["config"])).eval()
model.load_state_dict(ckpt["model"])
chars = ckpt["chars"]
stoi = {c: i for i, c in enumerate(chars)}
encode = lambda s: [stoi[c] for c in s if c in stoi]
decode = lambda ids: "".join(chars[i] for i in ids)
show = lambda c: repr(c)[1:-1] if c in "\n " else c        # make newline and space visible

prompt = "ROMEO:\nWhat light through yonder window b"
with torch.no_grad():
    logits = model(torch.tensor([encode(prompt)]))[0][:, -1, :]
probs = F.softmax(logits, dim=-1)[0]
top = torch.topk(probs, 8)
print(f"next-character probabilities after {prompt!r}:")
bars(top.values, [show(chars[i]) for i in top.indices])

prompt = "ROMEO:\n"
settings = [
    ("greedy", dict(greedy=True)),
    ("temperature 0.5", dict(temperature=0.5)),
    ("temperature 1.0", dict(temperature=1.0)),
    ("temperature 1.5", dict(temperature=1.5)),
    ("top-k 5", dict(top_k=5)),
    ("top-p 0.9", dict(top_p=0.9)),
]
for name, kw in settings:
    torch.manual_seed(7)                                       # same dice for every setting, a fair comparison
    out = model.generate(torch.tensor([encode(prompt)]), 120, **kw)
    text = decode(out[0].tolist())[len(prompt):]
    print(f"\n--- {name} ---\n{text}")
