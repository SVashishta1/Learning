"""Lesson 16, part 2: the KV cache. Prove it gives the same text, then measure the speed-up.

python kv_cache.py                 # ~1 minute on a laptop CPU
python kv_cache.py --tokens 600    # longer generations -> bigger speed-up
"""
import argparse
import os
import time

import torch

from model import GPT, GPTConfig, KVCache

p = argparse.ArgumentParser()
p.add_argument("--ckpt", default="../14-build-gpt-from-scratch/ckpt.pt")
p.add_argument("--tokens", type=int, default=200, help="how many tokens to generate in the speed test")
args = p.parse_args()
torch.manual_seed(0)

# ----------------------------------------------------------------------------- 1. same answers?
print("1) Correctness: greedy generation with and without the cache must be identical")
if os.path.exists(args.ckpt):
    ckpt = torch.load(args.ckpt, map_location="cpu")
    model = GPT(GPTConfig(**ckpt["config"])).eval()
    model.load_state_dict(ckpt["model"])
    chars = ckpt["chars"]
    print("   (using lesson 14's trained model)")
else:
    model = GPT(GPTConfig()).eval()
    chars = [chr(32 + i) for i in range(65)]
    print("   (no lesson 14 checkpoint found: using random weights, the test still works)")
prompt = torch.tensor([[chars.index(c) if c in chars else 0 for c in "ROMEO:\n"]])
n_new = 2 * model.cfg.block_size                               # long enough to also test a full window
slow = model.generate(prompt, n_new, greedy=True, use_cache=False)
fast = model.generate(prompt, n_new, greedy=True, use_cache=True)
print(f"   {n_new} tokens each | identical: {torch.equal(slow, fast)}")
print("   text:", repr("".join(chars[i] for i in fast[0].tolist())[:80]), "...")

# ----------------------------------------------------------------------------- 2. how much faster?
cfg = GPTConfig(vocab_size=65, block_size=1024, n_layer=6, n_head=6, n_embd=384)   # lesson 14's "video" size
model = GPT(cfg).eval()
print(f"\n2) Speed: {model.num_params() / 1e6:.1f}M-parameter model (random weights; speed doesn't depend on them), "
      f"generating {args.tokens} tokens")
start = torch.zeros((1, 1), dtype=torch.long)
results = {}
for use_cache in (False, True):
    t0 = time.time()
    model.generate(start, args.tokens, greedy=True, use_cache=use_cache)
    results[use_cache] = time.time() - t0
    name = "with cache   " if use_cache else "without cache"
    print(f"   {name}: {results[use_cache]:6.2f} s  = {args.tokens / results[use_cache]:6.1f} tokens/s")
print(f"   speed-up: {results[False] / results[True]:.1f}x")

# ----------------------------------------------------------------------------- 3. what does it cost?
cache = KVCache(cfg.n_layer)
with torch.no_grad():
    model(torch.zeros((1, args.tokens), dtype=torch.long), cache=cache)
print(f"\n3) Memory: the cache for {args.tokens} tokens holds {cache.megabytes():.1f} MB "
      f"(2 tensors x {cfg.n_layer} layers x {args.tokens} tokens x {cfg.n_embd} numbers x 4 bytes)")
print("   Work per new token: without cache ~ the whole text so far; with cache ~ one token.")
