"""Lesson 10, exercise 4: train the MLP + BatchNorm model using ONLY our own gradients.

No loss.backward() anywhere in the training loop: we compute every gradient with the
fast formulas from exercises 2 and 3 and update the parameters ourselves.
On the first step we still ask PyTorch, once, to double-check our gradients.

Usage:  python train_manual.py                 (50,000 steps, about a minute)
        python train_manual.py --steps 200000  (the video's length)
"""
import argparse
import random

import torch
import torch.nn.functional as F

from backprop_ninja import BLOCK_SIZE, N_EMBD, N_HIDDEN, VOCAB, fast_dhprebn, fast_dlogits, make_params
from names_data import load_words

torch.set_num_threads(1)   # tiny matrices: one CPU thread is fastest

parser = argparse.ArgumentParser()
parser.add_argument("--steps", type=int, default=50_000)
args = parser.parse_args()

words = load_words()
chars = sorted(set("".join(words)))
stoi = {s: i + 1 for i, s in enumerate(chars)}
stoi["."] = 0
itos = {i: s for s, i in stoi.items()}


def build_dataset(ws):
    X, Y = [], []
    for w in ws:
        context = [0] * BLOCK_SIZE
        for ch in w + ".":
            X.append(context)
            Y.append(stoi[ch])
            context = context[1:] + [stoi[ch]]
    return torch.tensor(X), torch.tensor(Y)


random.seed(42)
random.shuffle(words)
n1, n2 = int(0.8 * len(words)), int(0.9 * len(words))
Xtr, Ytr = build_dataset(words[:n1])
Xdev, Ydev = build_dataset(words[n1:n2])

P = make_params()
names = ["C", "W1", "b1", "W2", "b2", "bngain", "bnbias"]
print(f"parameters: {sum(P[k].nelement() for k in names):,}")
g = torch.Generator().manual_seed(2147483647)
n = 32

for step in range(args.steps):
    ix = torch.randint(0, Xtr.shape[0], (n,), generator=g)
    Xb, Yb = Xtr[ix], Ytr[ix]

    # ---- forward (the compact version) ----
    emb = P["C"][Xb]
    embcat = emb.view(n, -1)
    hprebn = embcat @ P["W1"] + P["b1"]
    bnmean = hprebn.mean(0, keepdim=True)
    bnvar = hprebn.var(0, keepdim=True, unbiased=True)
    bnvar_inv = (bnvar + 1e-5) ** -0.5
    bnraw = (hprebn - bnmean) * bnvar_inv
    hpreact = P["bngain"] * bnraw + P["bnbias"]
    h = torch.tanh(hpreact)
    logits = h @ P["W2"] + P["b2"]
    loss = F.cross_entropy(logits, Yb)

    # ---- backward, by hand ----
    with torch.no_grad():
        dlogits = fast_dlogits(logits, Yb)                       # exercise 2
        grads = {"W2": h.T @ dlogits, "b2": dlogits.sum(0)}
        dh = dlogits @ P["W2"].T
        dhpreact = (1.0 - h**2) * dh
        grads["bngain"] = (bnraw * dhpreact).sum(0, keepdim=True)
        grads["bnbias"] = dhpreact.sum(0, keepdim=True)
        dhprebn = fast_dhprebn(P["bngain"], bnvar_inv, bnraw, dhpreact)   # exercise 3
        grads["W1"] = embcat.T @ dhprebn
        grads["b1"] = dhprebn.sum(0)
        demb = (dhprebn @ P["W1"].T).view(emb.shape)
        grads["C"] = torch.zeros_like(P["C"]).index_add_(0, Xb.view(-1), demb.view(-1, N_EMBD))

    if step == 0:   # one-time check against PyTorch
        for k in names:
            P[k].grad = None
        loss.backward()
        worst = max((grads[k] - P[k].grad).abs().max().item() for k in names)
        print(f"step 0 check: biggest difference between our grads and PyTorch's = {worst:.1e}")

    lr = 0.1 if step < args.steps * 3 // 4 else 0.01
    with torch.no_grad():
        for k in names:
            P[k] += -lr * grads[k]                               # our own update, with our own gradients
    if step % (args.steps // 5) == 0:
        print(f"step {step:6d}/{args.steps}  loss {loss.item():.4f}")

# ---- after training: BatchNorm statistics of the whole training set, then evaluate ----
with torch.no_grad():
    hpre_all = P["C"][Xtr].view(Xtr.shape[0], -1) @ P["W1"] + P["b1"]
    bnmean_all = hpre_all.mean(0, keepdim=True)
    bnvar_all = hpre_all.var(0, keepdim=True, unbiased=True)

    def evaluate(X, Y):
        hpre = P["C"][X].view(X.shape[0], -1) @ P["W1"] + P["b1"]
        hpre = P["bngain"] * (hpre - bnmean_all) * (bnvar_all + 1e-5) ** -0.5 + P["bnbias"]
        return F.cross_entropy(torch.tanh(hpre) @ P["W2"] + P["b2"], Y).item()

    print(f"\ntrain loss {evaluate(Xtr, Ytr):.4f}   dev loss {evaluate(Xdev, Ydev):.4f}")

    g = torch.Generator().manual_seed(2147483647 + 10)
    print("names from a network trained with 100% hand-written gradients:")
    for _ in range(10):
        out, context = [], [0] * BLOCK_SIZE
        while True:
            hpre = P["C"][torch.tensor([context])].view(1, -1) @ P["W1"] + P["b1"]
            hpre = P["bngain"] * (hpre - bnmean_all) * (bnvar_all + 1e-5) ** -0.5 + P["bnbias"]
            probs = F.softmax(torch.tanh(hpre) @ P["W2"] + P["b2"], dim=1)
            ix = torch.multinomial(probs, num_samples=1, generator=g).item()
            context = context[1:] + [ix]
            if ix == 0:
                break
            out.append(itos[ix])
        print("  " + "".join(out))
