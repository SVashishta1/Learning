"""Generate text from a trained checkpoint:  python generate.py "JULIET:" 500"""
import sys

import torch

from model import GPT, Config

ckpt = torch.load("ckpt.pt", map_location="cpu")
model = GPT(Config(**ckpt["config"])); model.load_state_dict(ckpt["model"]); model.eval()
stoi = {c: i for i, c in enumerate(ckpt["chars"])}
prompt = sys.argv[1] if len(sys.argv) > 1 else "\n"
n = int(sys.argv[2]) if len(sys.argv) > 2 else 500
out = model.generate(torch.tensor([[stoi[c] for c in prompt if c in stoi]]), n, temperature=0.8, top_k=20)
print("".join(ckpt["chars"][i] for i in out[0].tolist()))
