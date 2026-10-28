"""Lesson 07, part 1: a bigram language model made by COUNTING.

"Bigram" = a pair of neighbouring characters. We count how often each character follows
each other character in 32,000 names, turn the counts into probabilities, and then:
  - generate new names one character at a time,
  - measure how good the model is with the negative log likelihood (the "loss").

Usage:  python bigram_counts.py          (a few seconds)
        python bigram_counts.py --plot   (also saves bigram_counts.png; needs matplotlib)
"""
import argparse

import torch

from names_data import load_words

parser = argparse.ArgumentParser()
parser.add_argument("--plot", action="store_true", help="save a picture of the 27x27 count table")
args = parser.parse_args()

# ---- 1. Look at the data ----
words = load_words()
print(f"{len(words)} names. First ten: {words[:10]}")
print(f"shortest: {min(len(w) for w in words)} letters, longest: {max(len(w) for w in words)} letters")

# ---- 2. Count bigrams in a Python dictionary ----
# "." marks both the start and the end of a name, so "emma" gives .e em mm ma a.
counts = {}
for w in words:
    chs = ["."] + list(w) + ["."]
    for ch1, ch2 in zip(chs, chs[1:]):                  # zip pairs each character with the next one
        counts[(ch1, ch2)] = counts.get((ch1, ch2), 0) + 1
top = sorted(counts.items(), key=lambda kv: -kv[1])[:8]
print("most common bigrams:", ", ".join(f"{a}{b}:{n}" for (a, b), n in top))

# ---- 3. The same counts in a 27x27 tensor (much faster to use) ----
chars = sorted(set("".join(words)))
stoi = {s: i + 1 for i, s in enumerate(chars)}          # string -> integer: a=1 ... z=26
stoi["."] = 0                                           # the special start/end token gets 0
itos = {i: s for s, i in stoi.items()}                  # integer -> string
V = len(stoi)                                           # vocabulary size: 27
N = torch.zeros((V, V), dtype=torch.int32)              # N[i, j] = how often char j follows char i
for w in words:
    chs = ["."] + list(w) + ["."]
    for ch1, ch2 in zip(chs, chs[1:]):
        N[stoi[ch1], stoi[ch2]] += 1
print(f"\ncount table N has shape {tuple(N.shape)}; row '.' = how names START:")
print("  " + "  ".join(f"{itos[j]}:{N[0, j].item()}" for j in range(1, V)))

if args.plot:
    import matplotlib
    matplotlib.use("Agg")                               # draw to a file, no window needed
    import matplotlib.pyplot as plt
    plt.figure(figsize=(16, 16))
    plt.imshow(N, cmap="Blues")
    for i in range(V):
        for j in range(V):
            plt.text(j, i, itos[i] + itos[j], ha="center", va="bottom", color="gray")
            plt.text(j, i, N[i, j].item(), ha="center", va="top", color="gray")
    plt.axis("off")
    plt.savefig("bigram_counts.png", bbox_inches="tight")
    print("saved bigram_counts.png")

# ---- 4. Counts -> probabilities (each row adds up to 1) ----
P = (N + 1).float()                                     # +1 "smoothing": no pair is ever impossible
P /= P.sum(1, keepdim=True)                             # (27, 27) / (27, 1): broadcasting divides each row by its own sum
print(f"\nrow sums (should all be 1): {P.sum(1)[:5].tolist()} ...")
print(f"P(next = 'a' | current = '.') = {P[0, stoi['a']]:.4f}")

# ---- 5. Sample new names: start at ".", repeatedly draw the next char from that row ----
g = torch.Generator().manual_seed(2147483647)           # fixed seed -> the same "random" names every run
print("\nnames invented by the bigram model:")
for _ in range(10):
    out, ix = [], 0
    while True:
        ix = torch.multinomial(P[ix], num_samples=1, replacement=True, generator=g).item()
        if ix == 0:                                     # drew the end token: the name is finished
            break
        out.append(itos[ix])
    print("  " + "".join(out))

# Compare with a model that knows NOTHING: every character equally likely.
g = torch.Generator().manual_seed(2147483647)
uniform = torch.ones(V) / V
print("names from a model that knows nothing (uniform):",
      ["".join(itos[i] for i in torch.multinomial(uniform, 8, replacement=True, generator=g).tolist()) for _ in range(3)])

# ---- 6. Loss: the average negative log likelihood of all the real bigrams ----
log_likelihood, n = 0.0, 0
for w in words:
    chs = ["."] + list(w) + ["."]
    for ch1, ch2 in zip(chs, chs[1:]):
        log_likelihood += torch.log(P[stoi[ch1], stoi[ch2]])
        n += 1
nll = -log_likelihood / n
print(f"\nlog likelihood of the whole dataset: {log_likelihood.item():.2f}")
print(f"average negative log likelihood (the LOSS): {nll.item():.4f}   (over {n} bigrams)")
print(f"for comparison, the know-nothing model scores -ln(1/27) = {torch.log(torch.tensor(27.0)).item():.4f}")

for test in ["andrej", "emma", "andrejq"]:
    chs = ["."] + list(test) + ["."]
    probs = [P[stoi[a], stoi[b]].item() for a, b in zip(chs, chs[1:])]
    loss = -sum(torch.log(torch.tensor(probs))).item() / len(probs)
    worst = min(zip(probs, zip(chs, chs[1:])))
    print(f"loss of '{test}': {loss:.4f}  (least likely pair: '{worst[1][0]}{worst[1][1]}' with p = {worst[0]:.5f})")
