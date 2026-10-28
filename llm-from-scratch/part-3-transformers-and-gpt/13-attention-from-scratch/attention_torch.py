"""Lesson 13, part 2: the same attention in PyTorch, then the fast "all heads at once" version,
then a tiny experiment where attention LEARNS where to look.

python attention_torch.py      (run attention_numpy.py first for the NumPy-vs-PyTorch check)
"""
import os

import numpy as np
import torch
from torch import nn
from torch.nn import functional as F

torch.manual_seed(1337)


def title(s):
    print("\n" + "=" * 70 + f"\n{s}\n" + "=" * 70)


# ----------------------------------------------------------------------------- 1. the averaging trick, 3 ways
title("1) 'Average the past' three ways (they must give the same numbers)")
B, T, C = 4, 8, 2
x = torch.randn(B, T, C)
# version 1: plain loops (slow but obvious)
xbow = torch.zeros(B, T, C)
for b in range(B):
    for t in range(T):
        xbow[b, t] = x[b, :t + 1].mean(dim=0)          # average of tokens 0..t
# version 2: one matrix multiply with a lower-triangular weight matrix
wei = torch.tril(torch.ones(T, T))
wei = wei / wei.sum(dim=1, keepdim=True)
xbow2 = wei @ x                                       # (T, T) @ (B, T, C) -> (B, T, C)
# version 3: scores of 0, future set to -inf, softmax  (this is the shape attention uses)
tril = torch.tril(torch.ones(T, T))
wei = torch.zeros(T, T).masked_fill(tril == 0, float("-inf"))
wei = F.softmax(wei, dim=-1)
xbow3 = wei @ x
print("loops == matmul:", torch.allclose(xbow, xbow2, atol=1e-6), "| loops == softmax:", torch.allclose(xbow, xbow3, atol=1e-6))
print("softmax weights (row t averages tokens 0..t):\n", wei[:4, :4])
print("In version 3 the zeros are fixed. Self-attention replaces them with learned scores q·k.")


# ----------------------------------------------------------------------------- 2. one head as a module
class Head(nn.Module):
    """One head of causal self-attention, exactly like attention_numpy.py section 4."""

    def __init__(self, n_embd, head_size, block_size, dropout=0.0):
        super().__init__()
        self.key = nn.Linear(n_embd, head_size, bias=False)      # a Linear without bias is just "x @ W"
        self.query = nn.Linear(n_embd, head_size, bias=False)
        self.value = nn.Linear(n_embd, head_size, bias=False)
        self.register_buffer("tril", torch.tril(torch.ones(block_size, block_size)))  # a constant, not learned
        self.dropout = nn.Dropout(dropout)

    def forward(self, x):
        B, T, C = x.shape
        k, q, v = self.key(x), self.query(x), self.value(x)        # each (B, T, head_size)
        wei = q @ k.transpose(-2, -1) * k.shape[-1] ** -0.5        # (B, T, hs) @ (B, hs, T) -> (B, T, T)
        wei = wei.masked_fill(self.tril[:T, :T] == 0, float("-inf"))
        wei = self.dropout(F.softmax(wei, dim=-1))
        self.last_weights = wei.detach()                           # kept so we can look at it later
        return wei @ v                                             # (B, T, T) @ (B, T, hs) -> (B, T, hs)


title("2) One head in PyTorch gives the same numbers as NumPy")
if os.path.exists("numpy_attention.npz"):
    d = np.load("numpy_attention.npz")
    head = Head(n_embd=8, head_size=4, block_size=4)
    with torch.no_grad():                                          # nn.Linear stores W transposed: (out, in)
        head.query.weight.copy_(torch.tensor(d["Wq"]).T)
        head.key.weight.copy_(torch.tensor(d["Wk"]).T)
        head.value.weight.copy_(torch.tensor(d["Wv"]).T)
    with torch.no_grad():
        out = head(torch.tensor(d["X"], dtype=torch.float32).unsqueeze(0))   # add a batch dimension: (1, T, C)
    print("max difference vs NumPy:", float((out[0] - torch.tensor(d["out"])).abs().max()))
else:
    print("(run attention_numpy.py first to create numpy_attention.npz)")


# ----------------------------------------------------------------------------- 3. multi-head, two ways
class MultiHeadAttention(nn.Module):
    """Readable version: a Python list of heads, outputs glued together, then mixed by `proj`."""

    def __init__(self, n_embd, n_head, block_size):
        super().__init__()
        self.heads = nn.ModuleList([Head(n_embd, n_embd // n_head, block_size) for _ in range(n_head)])
        self.proj = nn.Linear(n_embd, n_embd)

    def forward(self, x):
        return self.proj(torch.cat([h(x) for h in self.heads], dim=-1))


class CausalSelfAttention(nn.Module):
    """Fast version used in real GPTs: one big matrix makes q, k, v for ALL heads at once,
    and the heads are treated like an extra batch dimension."""

    def __init__(self, n_embd, n_head):
        super().__init__()
        self.n_head = n_head
        self.c_attn = nn.Linear(n_embd, 3 * n_embd, bias=False)   # [Wq | Wk | Wv] for every head, side by side
        self.c_proj = nn.Linear(n_embd, n_embd)

    def forward(self, x, verbose=False):
        B, T, C = x.shape
        nh, hs = self.n_head, C // self.n_head
        q, k, v = self.c_attn(x).split(C, dim=2)                  # each (B, T, C)
        q = q.view(B, T, nh, hs).transpose(1, 2)                   # (B, T, C) -> (B, T, nh, hs) -> (B, nh, T, hs)
        k = k.view(B, T, nh, hs).transpose(1, 2)
        v = v.view(B, T, nh, hs).transpose(1, 2)
        att = (q @ k.transpose(-2, -1)) * hs ** -0.5               # (B, nh, T, T)
        mask = torch.tril(torch.ones(T, T, dtype=torch.bool, device=x.device))
        att = F.softmax(att.masked_fill(~mask, float("-inf")), dim=-1)
        y = att @ v                                                # (B, nh, T, hs)
        y = y.transpose(1, 2).contiguous().view(B, T, C)           # glue heads back: (B, T, nh*hs) = (B, T, C)
        if verbose:
            print(f"x {tuple(x.shape)} -> q,k,v each {tuple(q.shape)} -> att {tuple(att.shape)} "
                  f"-> heads {tuple((att @ v).shape)} -> glued {tuple(y.shape)}")
        return self.c_proj(y)


title("3) Readable multi-head == fast multi-head == PyTorch's built-in fused attention")
B, T, C, nh = 2, 6, 16, 4
x = torch.randn(B, T, C)
slow = MultiHeadAttention(C, nh, block_size=T)
fast = CausalSelfAttention(C, nh)
with torch.no_grad():                                              # give the fast version the same weights
    Wq = torch.cat([h.query.weight for h in slow.heads])           # stack each head's rows: (C, C)
    Wk = torch.cat([h.key.weight for h in slow.heads])
    Wv = torch.cat([h.value.weight for h in slow.heads])
    fast.c_attn.weight.copy_(torch.cat([Wq, Wk, Wv]))
    fast.c_proj.load_state_dict(slow.proj.state_dict())
y_slow, y_fast = slow(x), fast(x, verbose=True)
print("readable vs fast, max difference:", float((y_slow - y_fast).abs().max()))
q, k, v = (t.view(B, T, nh, C // nh).transpose(1, 2) for t in fast.c_attn(x).split(C, dim=2))
y_sdpa = F.scaled_dot_product_attention(q, k, v, is_causal=True).transpose(1, 2).reshape(B, T, C)
print("fast vs F.scaled_dot_product_attention, max difference:", float((fast.c_proj(y_sdpa) - y_fast).abs().max()))
y_fast.sum().backward()
print("gradients reach the weights:", fast.c_attn.weight.grad.shape, "grad norm", round(float(fast.c_attn.weight.grad.norm()), 3))


# ----------------------------------------------------------------------------- 4. attention learns where to look
title("4) Training: can one head learn 'copy the token from 2 steps ago'?")
V_SIZE, T = 10, 8                                                  # 10 possible tokens, sequences of 8


class Copier(nn.Module):
    def __init__(self, n_embd=32):
        super().__init__()
        self.tok = nn.Embedding(V_SIZE, n_embd)                    # WHAT each token is
        self.pos = nn.Embedding(T, n_embd)                         # WHERE it is (attention alone ignores order)
        self.head = Head(n_embd, n_embd, block_size=T)
        self.out = nn.Linear(n_embd, V_SIZE)

    def forward(self, idx):
        x = self.tok(idx) + self.pos(torch.arange(idx.shape[1]))
        return self.out(self.head(x))


model = Copier()
opt = torch.optim.AdamW(model.parameters(), lr=3e-3)
for step in range(301):
    seq = torch.randint(V_SIZE, (64, T))
    logits = model(seq)[:, 2:]                                     # positions 0 and 1 have nothing 2 steps back
    loss = F.cross_entropy(logits.reshape(-1, V_SIZE), seq[:, :-2].reshape(-1))
    opt.zero_grad()
    loss.backward()
    opt.step()
    if step % 100 == 0:
        acc = (logits.argmax(-1) == seq[:, :-2]).float().mean()
        print(f"step {step:3d} | loss {loss.item():.3f} | accuracy {acc:.0%}")

model(torch.randint(V_SIZE, (1, T)))
print("\nlearned attention weights (row = position looking, column = position looked at):")
print("      " + "".join(f"{j:6d}" for j in range(T)))
for i, row in enumerate(model.head.last_weights[0]):
    print(f"{i:4d}  " + "".join(f"{float(v):6.2f}" for v in row))
print("From row 2 on, the weight sits 2 columns left of the diagonal: the head learned WHERE to look.")
