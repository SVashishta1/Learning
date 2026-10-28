"""Lesson 13, part 1: attention from scratch with NumPy, one idea at a time.

python attention_numpy.py
Every step prints its numbers and the SHAPE of every array (shape = how many rows, columns, ...).
"""
import numpy as np

np.set_printoptions(precision=2, suppress=True)
rng = np.random.default_rng(0)


def title(s):
    print("\n" + "=" * 70 + f"\n{s}\n" + "=" * 70)


# ----------------------------------------------------------------------------- 1. dot product
title("1) The dot product: a 'how similar are we?' score")
cat = np.array([0.9, 0.8, 0.1])      # pretend meaning: [is-animal, is-pet, is-vehicle]
dog = np.array([0.8, 0.9, 0.0])
car = np.array([0.0, 0.1, 0.9])
print("cat·dog =", round(float(cat @ dog), 2), " (similar things -> big score)")
print("cat·car =", round(float(cat @ car), 2), " (different things -> small score)")
print("by hand: 0.9*0.8 + 0.8*0.9 + 0.1*0.0 =", round(0.9 * 0.8 + 0.8 * 0.9 + 0.1 * 0.0, 2))


# ----------------------------------------------------------------------------- 2. softmax
title("2) Softmax: turn any scores into percentages that add up to 1")


def softmax(z):
    z = z - z.max(axis=-1, keepdims=True)    # subtracting the max changes nothing in the result, but avoids huge e^z
    e = np.exp(z)
    return e / e.sum(axis=-1, keepdims=True)


scores = np.array([2.0, 1.0, 0.1])
print("scores        :", scores)
print("e^scores      :", np.exp(scores))
print("softmax       :", softmax(scores), " sum =", softmax(scores).sum())
print("softmax(10x)  :", softmax(10 * scores), " <- big scores make softmax 'pick one' (almost one-hot)")
print("softmax([2, 1, -inf]):", softmax(np.array([2.0, 1.0, -np.inf])), " <- -inf gets exactly 0%")


# ----------------------------------------------------------------------------- 3. averaging the past
title("3) The simplest 'attention': every token averages itself and the tokens before it")
T, C = 4, 2                                   # 4 tokens, each described by 2 numbers
x = rng.normal(size=(T, C)).round(1)
print("x (T=4 tokens, C=2 numbers each), shape", x.shape, "\n", x)
w = np.tril(np.ones((T, T)))                  # tril = lower triangle of ones: row t sees tokens 0..t
w = w / w.sum(axis=1, keepdims=True)          # each row sums to 1 -> an average
print("weights (row = token doing the looking), shape", w.shape, "\n", w)
print("weights @ x = running average, shape", (w @ x).shape, "\n", w @ x)
print("check row 2 by hand: mean of x[0], x[1], x[2] =", x[:3].mean(axis=0))


# ----------------------------------------------------------------------------- 4. self-attention, one head
title("4) Real self-attention: the weights are LEARNED and depend on the tokens (one head)")
words = ["the", "cat", "sat", "down"]
T, C, H = len(words), 8, 4                    # 4 tokens, 8 numbers per token (n_embd), head size 4
X = rng.normal(size=(T, C))                   # pretend token embeddings, shape (T, C)
Wq = rng.normal(size=(C, H)) / np.sqrt(C)     # these three matrices are what training learns
Wk = rng.normal(size=(C, H)) / np.sqrt(C)
Wv = rng.normal(size=(C, H)) / np.sqrt(C)
Q = X @ Wq    # query: "what am I looking for?"           (T, C) @ (C, H) -> (T, H)
K = X @ Wk    # key:   "what do I contain?"               (T, H)
V = X @ Wv    # value: "what will I hand over if chosen?" (T, H)
print(f"X {X.shape} -> Q {Q.shape}, K {K.shape}, V {V.shape}")

S = Q @ K.T                                   # every query dotted with every key: (T, H) @ (H, T) -> (T, T)
print("raw scores Q @ K.T, shape", S.shape, "\n", S)
S = S / np.sqrt(H)                            # scale (see section 5 for why)
mask = np.tril(np.ones((T, T))) == 0          # True above the diagonal = the future
S[mask] = -np.inf                             # causal mask: a token may not look at later tokens
print("scaled + masked scores\n", S)
A = softmax(S)                                # attention weights, each row sums to 1
print("attention weights A = softmax(scores), shape", A.shape)
print("          " + "".join(f"{w:>7s}" for w in words))
for wd, row in zip(words, A):
    print(f"{wd:>8s}  " + "".join(f"{v:7.2f}" for v in row))
out = A @ V                                   # (T, T) @ (T, H) -> (T, H): a weighted mix of values
print("output = A @ V, shape", out.shape, "-> one new vector per token, built from the tokens it may see")


# ----------------------------------------------------------------------------- 5. why divide by sqrt(H)
title("5) Why divide by sqrt(head_size)?")
for h in (4, 64, 512):
    q, k = rng.normal(size=(1000, h)), rng.normal(size=(1000, h))
    d = (q * k).sum(axis=1)                   # 1000 dot products of random vectors
    print(f"head size {h:4d}: spread (std) of q·k = {d.std():6.2f}   after / sqrt({h}) = {(d / np.sqrt(h)).std():.2f}")
print("Without scaling, bigger heads give bigger scores -> softmax becomes one-hot (section 2) -> learning stalls.")


# ----------------------------------------------------------------------------- 6. multi-head
title("6) Multi-head attention: several heads in parallel, then glue and mix")
n_head = 2
head_size = C // n_head                       # 8 numbers split into 2 heads of 4
heads = []
for h in range(n_head):
    wq, wk, wv = (rng.normal(size=(C, head_size)) / np.sqrt(C) for _ in range(3))
    s = (X @ wq) @ (X @ wk).T / np.sqrt(head_size)
    s[mask] = -np.inf
    heads.append(softmax(s) @ (X @ wv))       # each head: (T, head_size)
    print(f"head {h}: output shape {heads[-1].shape}")
concat = np.concatenate(heads, axis=-1)       # (T, n_head * head_size) = (T, C)
Wo = rng.normal(size=(C, C)) / np.sqrt(C)     # output projection: lets the heads' findings mix
y = concat @ Wo
print(f"concatenated {concat.shape} -> @ Wo {Wo.shape} -> y {y.shape}  (same shape as X, so layers can stack)")


# ----------------------------------------------------------------------------- 7. a batch
title("7) Batches: many sequences at once (shape B, T, C)")
B = 3
Xb = rng.normal(size=(B, T, C))
Sb = (Xb @ Wq) @ (Xb @ Wk).transpose(0, 2, 1) / np.sqrt(H)   # (B,T,H) @ (B,H,T) -> (B,T,T)
Sb[:, mask] = -np.inf                                         # same mask for every sequence
outb = softmax(Sb) @ (Xb @ Wv)                               # (B,T,T) @ (B,T,H) -> (B,T,H)
print(f"Xb {Xb.shape} -> scores {Sb.shape} -> out {outb.shape}")
print("sequences never mix: each one only attends inside itself. Saved X/weights for attention_torch.py check.")
np.savez("numpy_attention.npz", X=X, Wq=Wq, Wk=Wk, Wv=Wv, out=out)
