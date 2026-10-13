"""Project 6.1: self-attention, the core of every transformer, by hand in NumPy.

Each word asks a QUESTION (query), advertises what it CONTAINS (key), and offers INFORMATION (value).
Attention weight = how well my question matches your key. My new meaning = weighted mix of everyone's values.
"""
import numpy as np

np.set_printoptions(precision=2, suppress=True)
rng = np.random.default_rng(0)

words = ["the", "cat", "sat", "on", "the", "mat"]
T, d_model, d_head = len(words), 8, 4

# Pretend embeddings (in a real model these are learned). The two "the"s share an embedding.
emb_table = {w: rng.normal(0, 1, d_model) for w in set(words)}
X = np.stack([emb_table[w] for w in words])          # (T, d_model) = (6, 8)

# Learned projection matrices (random here, trained in 6.2)
Wq, Wk, Wv = (rng.normal(0, 0.5, (d_model, d_head)) for _ in range(3))
Q, K, V = X @ Wq, X @ Wk, X @ Wv                     # each (6, 4)


def softmax(z):
    z = z - z.max(axis=-1, keepdims=True)             # subtract max for numerical stability
    e = np.exp(z)
    return e / e.sum(axis=-1, keepdims=True)


# 1. Scores: every word's query dotted with every word's key -> (6, 6) table
scores = Q @ K.T / np.sqrt(d_head)                    # scale by sqrt(d) so softmax doesn't saturate
# 2. Causal mask: a GPT may only look at PAST words (it can't peek at the word it's trying to predict)
mask = np.triu(np.ones((T, T)), k=1).astype(bool)
scores[mask] = -np.inf
# 3. Softmax each row -> attention weights that sum to 1
weights = softmax(scores)
# 4. Mix the values
out = weights @ V                                     # (6, 6) @ (6, 4) -> (6, 4)

print("Attention weights (row = word looking, column = word looked at):")
print("        " + "".join(f"{w:>6s}" for w in words))
for w, row in zip(words, weights):
    print(f"{w:>6s}  " + "".join(f"{v:6.2f}" for v in row))
print("\nNotice: the upper triangle is 0 (no peeking at the future), and every row sums to 1.")
print("output shape:", out.shape, "-> each word now carries context from the words before it")


# 5. Multi-head attention: several heads look for different relationships, then get concatenated
def attention_head(X, rng):
    Wq, Wk, Wv = (rng.normal(0, 0.5, (d_model, d_head)) for _ in range(3))
    s = (X @ Wq) @ (X @ Wk).T / np.sqrt(d_head)
    s[mask] = -np.inf
    return softmax(s) @ (X @ Wv)


heads = [attention_head(X, rng) for _ in range(2)]
Wo = rng.normal(0, 0.5, (2 * d_head, d_model))
multi = np.concatenate(heads, axis=-1) @ Wo           # (6, 8): same shape as the input, ready for the next layer
print("multi-head output shape:", multi.shape, "(same as input, so blocks can be stacked)")
