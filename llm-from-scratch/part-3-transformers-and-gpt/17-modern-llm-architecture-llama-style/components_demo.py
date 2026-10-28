"""Lesson 17, part 1: each LLaMA ingredient on its own, with numbers you can check.

python components_demo.py      (instant, no training)
"""
import torch
from torch import nn
from torch.nn import functional as F

from model import GPT, Config, RMSNorm, SwiGLU, GeluMLP, apply_rope, rope_cos_sin, GPT2_STYLE, LLAMA_STYLE

torch.manual_seed(0)
torch.set_printoptions(precision=3, sci_mode=False)


def title(s):
    print("\n" + "=" * 70 + f"\n{s}\n" + "=" * 70)


# ----------------------------------------------------------------------------- 1. RMSNorm
title("1) LayerNorm vs RMSNorm on one token's vector")
x = torch.tensor([[2.0, 4.0, 6.0, 8.0]])
ln, rms = nn.LayerNorm(4), RMSNorm(4)
print("x                 :", x[0].tolist())
print("mean, RMS of x    :", x.mean().item(), round(x.pow(2).mean().sqrt().item(), 3))
print("LayerNorm(x)      :", ln(x)[0].detach(), " <- (x - mean) / std: centred at 0")
print("RMSNorm(x)        :", rms(x)[0].detach(), " <- x / RMS: same direction, just resized")
print("RMS of RMSNorm(x) :", round(rms(x).pow(2).mean().sqrt().item(), 3), "(always ~1, like LayerNorm's std)")

# ----------------------------------------------------------------------------- 2. RoPE
title("2) RoPE: rotate queries and keys by their position")
hs = 8
cos, sin = rope_cos_sin(200, hs)                       # angles for positions 0..199
q, k = torch.randn(hs), torch.randn(hs)


def score(m, n):
    """dot product of q placed at position m and k placed at position n"""
    qm = apply_rope(q.view(1, 1, 1, hs), cos[m], sin[m]).flatten()
    kn = apply_rope(k.view(1, 1, 1, hs), cos[n], sin[n]).flatten()
    return (qm @ kn).item()


for m, n in [(3, 1), (10, 8), (150, 148), (3, 2), (10, 2)]:
    print(f"q at position {m:3d}, k at position {n:3d} (distance {m - n}): score {score(m, n):7.3f}")
print("Same distance -> same score, wherever the pair sits: attention 'feels' RELATIVE position.")
q5 = apply_rope(q.view(1, 1, 1, hs), cos[5], sin[5]).flatten()
print(f"length before/after rotating: {q.norm():.3f} / {q5.norm():.3f} (rotation never changes the length)")

# ----------------------------------------------------------------------------- 3. SwiGLU
title("3) SwiGLU: an MLP with a gate")
z = torch.tensor([-3.0, -1.0, 0.0, 1.0, 3.0])
print("z        :", z.tolist())
print("GELU(z)  :", F.gelu(z))
print("SiLU(z)  :", F.silu(z), " (z * sigmoid(z): ~0 for negatives, ~z for positives)")
cfg = Config(n_embd=128)
for name, mlp in [("GELU MLP", GeluMLP(cfg)), ("SwiGLU", SwiGLU(Config(n_embd=128, bias=False)))]:
    shapes = [tuple(p.shape) for p in mlp.parameters() if p.dim() == 2]
    print(f"{name:9s}: {sum(p.numel() for p in mlp.parameters()):,} parameters, weight matrices {shapes}")

# ----------------------------------------------------------------------------- 4. GQA
title("4) Grouped-query attention: share keys/values between query heads")
print("Why: when generating, every layer keeps the keys and values of every past token (the KV cache, lesson 16).")
print("Example: a LLaMA-2-70B-shaped model, 80 layers, 64 query heads of size 128, 4,096 tokens, 16-bit numbers:")
for n_kv, name in [(64, "multi-head (MHA)"), (8, "grouped-query (GQA-8)"), (1, "multi-query (MQA)")]:
    gb = 2 * 80 * n_kv * 128 * 4096 * 2 / 1e9           # (K and V) x layers x kv heads x head size x tokens x bytes
    print(f"  {name:22s} {n_kv:2d} key/value heads -> KV cache {gb:6.2f} GB per sequence")
print("LLaMA 2 70B and LLaMA 3 use 8 key/value heads: 8x smaller cache, almost the same quality.")
for n_kv in (4, 2, 1):
    m = GPT(Config(n_head=4, n_kv_head=n_kv))
    print(f"  our model with 4 query heads, {n_kv} kv heads: {m.num_params():,} parameters, output {tuple(m(torch.zeros(2, 10, dtype=torch.long))[0].shape)}")

# ----------------------------------------------------------------------------- 5. both models
title("5) The two models compared in compare.py")
for name, style in [("GPT-2 style", GPT2_STYLE), ("LLaMA style", LLAMA_STYLE)]:
    m = GPT(Config(**style))
    print(f"{name}: {m.num_params():,} parameters  {style}")
