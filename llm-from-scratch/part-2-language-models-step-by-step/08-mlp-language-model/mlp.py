"""Lesson 08: an MLP (multi-layer perceptron) language model, following Bengio et al. 2003.

Instead of looking at ONE previous character (bigram), we look at the previous THREE.
Each character gets a learned "embedding" (a short list of numbers = its position on a map),
the three embeddings are joined together, sent through a hidden tanh layer,
and an output layer gives 27 scores for the next character.

Usage:  python mlp.py                       (200,000 steps like the video; about a minute on a laptop CPU)
        python mlp.py --steps 20000         (a quick 10x shorter run)
        python mlp.py --find-lr             (the learning-rate search from the video, then stop)
        python mlp.py --plot                (also save the 2-D picture of the letter embeddings)
"""
import argparse
import random
import time

import torch
import torch.nn.functional as F

from names_data import load_words

torch.set_num_threads(1)   # our matrices are tiny: one CPU thread is fastest (no time lost handing work between threads)

parser = argparse.ArgumentParser()
parser.add_argument("--steps", type=int, default=200_000)
parser.add_argument("--block-size", type=int, default=3, help="how many previous characters to look at")
parser.add_argument("--emb", type=int, default=10, help="numbers per character embedding")
parser.add_argument("--hidden", type=int, default=200, help="neurons in the hidden layer")
parser.add_argument("--batch-size", type=int, default=32)
parser.add_argument("--find-lr", action="store_true")
parser.add_argument("--plot", action="store_true")
args = parser.parse_args()

words = load_words()
chars = sorted(set("".join(words)))
stoi = {s: i + 1 for i, s in enumerate(chars)}
stoi["."] = 0
itos = {i: s for s, i in stoi.items()}
V = len(stoi)


def build_dataset(words, block_size, verbose=False):
    """Slide a window over every name: (3 previous chars) -> next char."""
    X, Y = [], []
    for w in words:
        context = [0] * block_size                     # start with "..." (all start tokens)
        for ch in w + ".":
            ix = stoi[ch]
            if verbose:
                print("  " + "".join(itos[i] for i in context), "--->", itos[ix])
            X.append(context)
            Y.append(ix)
            context = context[1:] + [ix]               # slide the window one step to the right
    return torch.tensor(X), torch.tensor(Y)


print("training examples made from 'emma':")
build_dataset(["emma"], args.block_size, verbose=True)

# ---- Split: 80% to train on, 10% "dev" to tune settings, 10% "test" to report at the very end ----
random.seed(42)
random.shuffle(words)
n1, n2 = int(0.8 * len(words)), int(0.9 * len(words))
Xtr, Ytr = build_dataset(words[:n1], args.block_size)
Xdev, Ydev = build_dataset(words[n1:n2], args.block_size)
Xte, Yte = build_dataset(words[n2:], args.block_size)
print(f"\ntrain {tuple(Xtr.shape)}  dev {tuple(Xdev.shape)}  test {tuple(Xte.shape)}")

# ---- The parameters ----
g = torch.Generator().manual_seed(2147483647)
C = torch.randn((V, args.emb), generator=g)                           # embedding table: one row per character
W1 = torch.randn((args.block_size * args.emb, args.hidden), generator=g)
b1 = torch.randn(args.hidden, generator=g)
W2 = torch.randn((args.hidden, V), generator=g)
b2 = torch.randn(V, generator=g)
parameters = [C, W1, b1, W2, b2]
for p in parameters:
    p.requires_grad = True
print(f"parameters: {sum(p.nelement() for p in parameters):,}")


def forward(X):
    emb = C[X]                                          # (B, 3) -> (B, 3, 10): look up each char's row in C
    h = torch.tanh(emb.view(emb.shape[0], -1) @ W1 + b1)   # join the 3 embeddings into 30 numbers -> hidden layer
    return h @ W2 + b2                                  # (B, 27) logits


@torch.no_grad()
def split_loss(X, Y):
    return F.cross_entropy(forward(X), Y).item()


if args.find_lr:
    # Try learning rates from 0.001 to 1, rising a little every step; watch where the loss is lowest.
    lrs = 10 ** torch.linspace(-3, 0, 1000)
    losses = []
    for i in range(1000):
        ix = torch.randint(0, Xtr.shape[0], (args.batch_size,), generator=g)
        loss = F.cross_entropy(forward(Xtr[ix]), Ytr[ix])
        for p in parameters:
            p.grad = None
        loss.backward()
        for p in parameters:
            p.data += -lrs[i] * p.grad
        losses.append(loss.item())
    print("\nlearning rate -> average loss over the 100 steps around it")
    for i in range(50, 1000, 100):
        window = losses[max(0, i - 50):i + 50]
        print(f"  lr {lrs[i]:.4f}  loss {sum(window) / len(window):.3f}")
    raise SystemExit("a good learning rate is where the loss is lowest before it shoots up (about 0.1)")

# ---- Training with mini-batches ----
start = time.time()
for step in range(args.steps):
    ix = torch.randint(0, Xtr.shape[0], (args.batch_size,), generator=g)   # 32 random examples
    loss = F.cross_entropy(forward(Xtr[ix]), Ytr[ix])  # softmax + negative log likelihood in one fast call
    for p in parameters:
        p.grad = None
    loss.backward()
    lr = 0.1 if step < args.steps // 2 else 0.01       # "learning rate decay": smaller steps for the second half
    for p in parameters:
        p.data += -lr * p.grad
    if step % (args.steps // 10) == 0:
        print(f"step {step:7d}/{args.steps}  batch loss {loss.item():.4f}  ({time.time() - start:.0f}s)")

print(f"\nfinal loss  train {split_loss(Xtr, Ytr):.4f}   dev {split_loss(Xdev, Ydev):.4f}")
print(f"(bigram model from lesson 07: about 2.45. Lower is better.)")
print(f"test loss, looked at only once at the very end: {split_loss(Xte, Yte):.4f}")

# ---- Sampling ----
g = torch.Generator().manual_seed(2147483647 + 10)
print("\nnames invented by the MLP:")
for _ in range(15):
    out, context = [], [0] * args.block_size
    while True:
        with torch.no_grad():
            probs = F.softmax(forward(torch.tensor([context])), dim=1)
        ix = torch.multinomial(probs, num_samples=1, generator=g).item()
        context = context[1:] + [ix]
        if ix == 0:
            break
        out.append(itos[ix])
    print("  " + "".join(out))

if args.plot:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    E = C.detach()
    # Squash the embeddings to 2-D for drawing (they are already 2-D if you ran with --emb 2).
    if E.shape[1] > 2:
        E = E - E.mean(0)
        _, _, Vt = torch.linalg.svd(E, full_matrices=False)   # the 2 directions where the points spread most
        E = E @ Vt[:2].T
    plt.figure(figsize=(8, 8))
    plt.scatter(E[:, 0], E[:, 1], s=200)
    for i in range(V):
        plt.text(E[i, 0].item(), E[i, 1].item(), itos[i], ha="center", va="center", color="white")
    plt.grid(True)
    plt.savefig("embeddings.png", bbox_inches="tight")
    print("saved embeddings.png")
