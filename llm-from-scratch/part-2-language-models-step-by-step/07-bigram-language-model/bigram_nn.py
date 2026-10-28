"""Lesson 07, part 2: the SAME bigram model, but learned by a neural network with gradient descent.

Input: the current character (as a one-hot vector of 27 numbers).
One linear layer: 27 inputs -> 27 outputs ("logits" = raw scores for the next character).
Softmax turns scores into probabilities; the loss is the average negative log likelihood.
After training, the network reaches almost the same loss as counting (about 2.45-2.48).

Usage:  python bigram_nn.py   (a few seconds)
"""
import torch
import torch.nn.functional as F

from names_data import load_words

words = load_words()
chars = sorted(set("".join(words)))
stoi = {s: i + 1 for i, s in enumerate(chars)}
stoi["."] = 0
itos = {i: s for s, i in stoi.items()}
V = len(stoi)

# ---- 1. The training set: every bigram becomes (input char index, target char index) ----
xs, ys = [], []
for w in words:
    chs = ["."] + list(w) + ["."]
    for ch1, ch2 in zip(chs, chs[1:]):
        xs.append(stoi[ch1])
        ys.append(stoi[ch2])
xs, ys = torch.tensor(xs), torch.tensor(ys)
num = xs.nelement()
print(f"{num} training examples, e.g. the first five pairs of 'emma':")
for x, y in zip(xs[:5].tolist(), ys[:5].tolist()):
    print(f"  input '{itos[x]}' ({x:2d})  ->  target '{itos[y]}' ({y:2d})")

# ---- 2. One-hot encoding: index 5 -> [0,0,0,0,0,1,0,...,0] (27 numbers) ----
xenc = F.one_hot(xs, num_classes=V).float()             # shape (num, 27); float so we can multiply it
print(f"one-hot inputs: shape {tuple(xenc.shape)}; row 0 has a 1 at position {xenc[0].argmax().item()}")

# ---- 3. The network: a 27x27 weight matrix, randomly initialised ----
g = torch.Generator().manual_seed(2147483647)
W = torch.randn((V, V), generator=g, requires_grad=True)

# ---- 4. Gradient descent ----
for k in range(201):
    logits = xenc @ W                                   # (num, 27) @ (27, 27): "log-counts" for every next char
    counts = logits.exp()                               # make them positive, like counts
    probs = counts / counts.sum(1, keepdim=True)        # normalise each row -> probabilities (this is softmax)
    data_loss = -probs[torch.arange(num), ys].log().mean()   # average NLL of the correct next chars
    reg_loss = 0.01 * (W**2).mean()                     # gentle pull of W towards 0 (= smoothing)
    loss = data_loss + reg_loss
    if k % 25 == 0:
        print(f"step {k:3d}  loss {loss.item():.4f}")
    W.grad = None                                       # zero the old gradient
    loss.backward()
    W.data += -50 * W.grad                              # learning rate 50: this simple problem tolerates huge steps

# ---- 5. Sample from the network (same seed as the counting model) ----
g = torch.Generator().manual_seed(2147483647)
print("\nnames invented by the neural bigram model:")
for _ in range(10):
    out, ix = [], 0
    while True:
        xenc1 = F.one_hot(torch.tensor([ix]), num_classes=V).float()
        p = F.softmax(xenc1 @ W, dim=1)                 # softmax = exp then normalise, in one call
        ix = torch.multinomial(p, num_samples=1, replacement=True, generator=g).item()
        if ix == 0:
            break
        out.append(itos[ix])
    print("  " + "".join(out))

# ---- 6. What did the network learn? Compare W with the log of the counts ----
N = torch.zeros((V, V))
for x, y in zip(xs.tolist(), ys.tolist()):
    N[x, y] += 1
P_counts = (N + 1) / (N + 1).sum(1, keepdim=True)
P_nn = F.softmax(W.detach(), dim=1)
print(f"\nP(next='a' | '.'): counting {P_counts[0, 1]:.4f}   network {P_nn[0, 1]:.4f}")
print(f"biggest difference between the two 27x27 probability tables: {(P_counts - P_nn).abs().max():.4f}")
