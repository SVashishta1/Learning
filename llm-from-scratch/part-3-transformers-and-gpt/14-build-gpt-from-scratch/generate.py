"""Lesson 14: write new "Shakespeare" with the model saved by train.py.

python generate.py                          # 500 characters starting with "ROMEO:"
python generate.py "JULIET:" 300 0.6        # prompt, number of characters, temperature
"""
import os
import sys

import torch

from gpt import GPT, GPTConfig

prompt = sys.argv[1] if len(sys.argv) > 1 else "ROMEO:"
n_chars = int(sys.argv[2]) if len(sys.argv) > 2 else 500
temperature = float(sys.argv[3]) if len(sys.argv) > 3 else 0.8

if not os.path.exists("ckpt.pt"):
    sys.exit("No ckpt.pt found. Train first:  python train.py")
ckpt = torch.load("ckpt.pt", map_location="cpu")
model = GPT(GPTConfig(**ckpt["config"]))
model.load_state_dict(ckpt["model"])
model.eval()

chars = ckpt["chars"]
stoi = {ch: i for i, ch in enumerate(chars)}
ids = [stoi[c] for c in prompt if c in stoi]                # characters Shakespeare never used are skipped
if not ids:
    sys.exit("The prompt has no characters the model knows.")
torch.manual_seed(42)
out = model.generate(torch.tensor([ids]), n_chars, temperature=temperature)
print("".join(chars[i] for i in out[0].tolist()))
