"""Project 5.2: a character-level BIGRAM model. It predicts the next letter from the current letter,
just by counting. Then it invents new names. This is a language model in ~30 lines."""
import numpy as np

from get_names import load_names

names = load_names()
print(f"{len(names)} names, e.g. {names[:6]}")

chars = sorted(set("".join(names)))
stoi = {c: i + 1 for i, c in enumerate(chars)}
stoi["."] = 0                                   # "." marks the START and END of a name
itos = {i: c for c, i in stoi.items()}
V = len(stoi)

# 1. COUNT: N[a, b] = how many times letter b follows letter a
N = np.zeros((V, V), dtype=np.int32)
for name in names:
    seq = ["."] + list(name) + ["."]
    for a, b in zip(seq, seq[1:]):
        N[stoi[a], stoi[b]] += 1

# 2. NORMALISE each row into probabilities (+1 smoothing so nothing is impossible)
P = (N + 1) / (N + 1).sum(axis=1, keepdims=True)

letter = "q" if "q" in stoi else names[0][0]   # the small fallback name list has no "q"
top3 = P[stoi[letter]].argsort()[::-1][:3]      # indices of the 3 biggest probabilities in that row
print(f"\nAfter '{letter}' the most likely next letters are:", [(itos[i], f"{P[stoi[letter], i]:.0%}") for i in top3])
print("Names most often start with:", [itos[i] for i in P[0].argsort()[::-1][:5]])

# 3. GENERATE: start at ".", sample the next letter from the probabilities, repeat until "."
rng = np.random.default_rng(42)
print("\nInvented names:")
for _ in range(12):
    out, ix = [], 0
    while True:
        ix = rng.choice(V, p=P[ix])
        if ix == 0:
            break
        out.append(itos[ix])
    print("  ", "".join(out))

# 4. EVALUATE: average negative log-likelihood (lower = less surprised by real names)
log_likelihood, n = 0.0, 0
for name in names:
    seq = ["."] + list(name) + ["."]
    for a, b in zip(seq, seq[1:]):
        log_likelihood += np.log(P[stoi[a], stoi[b]]); n += 1
print(f"\nloss (avg negative log-likelihood): {-log_likelihood / n:.3f}  (random guessing would be {np.log(V):.3f})")
