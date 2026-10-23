"""Lesson 09, part 1: why the starting numbers matter, and how BatchNorm helps.

We take lesson 08's MLP (3 chars -> 10-number embeddings -> 200 tanh neurons -> 27 scores) and:
  A. look at the loss BEFORE training: 27 (terrible) vs the 3.30 we should expect,
  B. look at the hidden tanh neurons: how many are "saturated" (stuck at -1 or +1),
  C. train four versions and compare: naive init -> fixed output -> Kaiming init -> + BatchNorm.

Usage:  python init_and_batchnorm.py                  (4 x 50,000 steps; about a minute or two)
        python init_and_batchnorm.py --steps 200000   (the video's length; slower, a bit better)
        python init_and_batchnorm.py --plot           (also save hidden_activations.png)
"""
import argparse
import math
import random

import torch
import torch.nn.functional as F

from names_data import load_words

torch.set_num_threads(1)   # tiny matrices: one CPU thread is fastest

parser = argparse.ArgumentParser()
parser.add_argument("--steps", type=int, default=50_000)
parser.add_argument("--plot", action="store_true")
args = parser.parse_args()

BLOCK, EMB, HIDDEN = 3, 10, 200
words = load_words()
chars = sorted(set("".join(words)))
stoi = {s: i + 1 for i, s in enumerate(chars)}
stoi["."] = 0
V = len(stoi)


def build_dataset(ws):
    X, Y = [], []
    for w in ws:
        context = [0] * BLOCK
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


def make_model(init, seed=2147483647):
    """init: 'naive' | 'fix_output' | 'kaiming' | 'batchnorm' (each one adds a fix to the previous)."""
    g = torch.Generator().manual_seed(seed)
    m = {"C": torch.randn((V, EMB), generator=g)}
    W1 = torch.randn((BLOCK * EMB, HIDDEN), generator=g)
    b1 = torch.randn(HIDDEN, generator=g)
    W2 = torch.randn((HIDDEN, V), generator=g)
    b2 = torch.randn(V, generator=g)
    if init != "naive":
        W2 = W2 * 0.01                    # small output weights -> logits near 0 -> every char ~1/27 at the start
        b2 = b2 * 0
    if init in ("kaiming", "batchnorm"):
        W1 = W1 * (5 / 3) / math.sqrt(BLOCK * EMB)   # Kaiming init: gain 5/3 for tanh, divided by sqrt(fan_in)
        b1 = b1 * 0.01
    m.update(W1=W1, b1=b1, W2=W2, b2=b2)
    if init == "batchnorm":
        m["bngain"] = torch.ones((1, HIDDEN))        # learnable scale, starts at 1
        m["bnbias"] = torch.zeros((1, HIDDEN))       # learnable shift, starts at 0
        m["bnmean_running"] = torch.zeros((1, HIDDEN))   # NOT trained by gradients: a running average
        m["bnstd_running"] = torch.ones((1, HIDDEN))
    for k in ("C", "W1", "b1", "W2", "b2", "bngain", "bnbias"):
        if k in m:
            m[k].requires_grad = True
    return m


def params(m):
    return [m[k] for k in ("C", "W1", "b1", "W2", "b2", "bngain", "bnbias") if k in m]


def forward(m, X, training):
    emb = m["C"][X].view(X.shape[0], -1)
    hpreact = emb @ m["W1"] + m["b1"]
    if "bngain" in m:
        if training:
            mean = hpreact.mean(0, keepdim=True)    # statistics of THIS batch
            std = hpreact.std(0, keepdim=True)
            with torch.no_grad():                   # keep a slow running average for use after training
                m["bnmean_running"].mul_(0.999).add_(0.001 * mean)
                m["bnstd_running"].mul_(0.999).add_(0.001 * std)
        else:
            mean, std = m["bnmean_running"], m["bnstd_running"]
        hpreact = m["bngain"] * (hpreact - mean) / (std + 1e-5) + m["bnbias"]
    h = torch.tanh(hpreact)
    return h @ m["W2"] + m["b2"], h, hpreact


# ---------------- A + B: look at the network BEFORE any training ----------------
g = torch.Generator().manual_seed(42)
ix = torch.randint(0, Xtr.shape[0], (32,), generator=g)
print(f"expected loss for a fair guess: -ln(1/27) = {-math.log(1 / 27):.4f}\n")
print(f"{'init':<11} {'first loss':>10} {'logit range':>13} {'|h|>0.99 (saturated)':>22} {'preact std':>11}")
first_h = {}
for init in ("naive", "fix_output", "kaiming", "batchnorm"):
    m = make_model(init)
    with torch.no_grad():
        logits, h, hpreact = forward(m, Xtr[ix], training=True)
        loss = F.cross_entropy(logits, Ytr[ix])
    first_h[init] = h
    print(f"{init:<11} {loss.item():10.4f} {logits.min().item():6.1f}..{logits.max().item():<5.1f} "
          f"{(h.abs() > 0.99).float().mean().item():21.1%} {hpreact.std().item():11.2f}")

if args.plot:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(1, 2, figsize=(12, 4))
    for ax, init in zip(axes, ("fix_output", "kaiming")):
        ax.hist(first_h[init].view(-1).tolist(), bins=50)
        ax.set_title(f"tanh outputs at the start: {init}")
    plt.savefig("hidden_activations.png", bbox_inches="tight")
    print("saved hidden_activations.png")

# ---------------- C: train each version and compare ----------------
print(f"\ntraining each version for {args.steps} steps (lr 0.1, then 0.01 for the second half)")
results = {}
for init in ("naive", "fix_output", "kaiming", "batchnorm"):
    m = make_model(init)
    g = torch.Generator().manual_seed(2147483647)
    for step in range(args.steps):
        ix = torch.randint(0, Xtr.shape[0], (32,), generator=g)
        logits, _, _ = forward(m, Xtr[ix], training=True)
        loss = F.cross_entropy(logits, Ytr[ix])
        for p in params(m):
            p.grad = None
        loss.backward()
        lr = 0.1 if step < args.steps // 2 else 0.01
        for p in params(m):
            p.data += -lr * p.grad
    with torch.no_grad():
        train_loss = F.cross_entropy(forward(m, Xtr, training=False)[0], Ytr).item()
        dev_loss = F.cross_entropy(forward(m, Xdev, training=False)[0], Ydev).item()
    results[init] = (train_loss, dev_loss)
    print(f"  {init:<11} train {train_loss:.4f}   dev {dev_loss:.4f}")

print("\nFixing the output and using Kaiming init each lower the dev loss: less time wasted at the start,")
print("fewer saturated neurons. BatchNorm lands close to Kaiming WITHOUT any careful maths. In a net this")
print("shallow it does not win (the video sees the same); it shines in deep nets (run diagnostics.py).")
