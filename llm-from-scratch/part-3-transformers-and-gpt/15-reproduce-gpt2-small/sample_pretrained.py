"""Lesson 15: load OpenAI's real GPT-2 (124M) weights into OUR gpt2.py and let it write.

python sample_pretrained.py
python sample_pretrained.py "The meaning of life is" --model gpt2-medium
Needs `pip install transformers tiktoken` and internet the first time (~550 MB download for gpt2,
cached afterwards in ~/.cache/huggingface).
"""
import argparse
import sys

import torch

from gpt2 import GPT

p = argparse.ArgumentParser()
p.add_argument("prompt", nargs="?", default="Hello, I'm a language model,")
p.add_argument("--model", default="gpt2", choices=["gpt2", "gpt2-medium", "gpt2-large", "gpt2-xl"])
p.add_argument("--samples", type=int, default=4)
p.add_argument("--tokens", type=int, default=30)
args = p.parse_args()

try:
    import tiktoken
    from transformers import GPT2LMHeadModel
    hf = GPT2LMHeadModel.from_pretrained(args.model).eval()     # OpenAI's weights, via the Hugging Face Hub
    enc = tiktoken.get_encoding("gpt2")
except Exception as e:                                         # no internet, blocked site, missing package...
    sys.exit(f"Could not load {args.model}: {type(e).__name__}: {e}\n"
             "Check: pip install transformers tiktoken, and that https://huggingface.co is reachable.")

model = GPT.from_hf_model(hf).eval()
n_params = sum(p.numel() for p in model.parameters())
print(f"loaded {args.model}: {n_params:,} parameters (embedding shared with the output layer)")

# 1. Proof that the copy is exact: both models must produce the same next-token scores.
idx = torch.tensor([enc.encode(args.prompt)])
with torch.no_grad():
    diff = (hf(idx).logits - model(idx)[0]).abs().max().item()
print(f"max difference between Hugging Face and our model's logits: {diff:.2e}")

# 2. What does it think comes next?
with torch.no_grad():
    probs = torch.softmax(model(idx)[0][0, -1], dim=-1)
top = torch.topk(probs, 5)
print("top 5 next tokens:", [(enc.decode([int(i)]), round(float(p), 3)) for p, i in zip(top.values, top.indices)])

# 3. Let it write (top-k 50 sampling, like Hugging Face's default).
torch.manual_seed(42)
out = model.generate(idx.repeat(args.samples, 1), args.tokens, top_k=50)
for row in out:
    print(">", enc.decode(row.tolist()).replace("\n", " "))
