"""Lesson 11: a deeper character model in the style of WaveNet (2016).

Context grows from 3 to 8 characters. Instead of squashing all 8 into one layer at once
(like lesson 08's MLP), we combine them gradually, in a tree:
    8 chars -> 4 pairs -> 2 pairs-of-pairs -> 1 summary -> next-char scores
Every layer here is our own class with the same name and behaviour as torch.nn's.

Usage:  python wavenet.py                     (WaveNet, 50,000 steps; about 2 minutes on a laptop CPU)
        python wavenet.py --steps 200000      (the video's full run, about 6-8 minutes; dev loss about 1.99)
        python wavenet.py --model flat        (lesson 08's plain MLP, but reading all 8 chars at once, to compare)
"""
import argparse
import random
import time

import torch
import torch.nn.functional as F

from names_data import load_words

torch.set_num_threads(1)   # small matrices: one CPU thread is usually fastest


# ----------------------------- the layers -----------------------------
class Linear:
    def __init__(self, fan_in, fan_out, bias=True):
        self.weight = torch.randn((fan_in, fan_out)) / fan_in**0.5     # Kaiming-style init (gain is set later)
        self.bias = torch.zeros(fan_out) if bias else None

    def __call__(self, x):
        self.out = x @ self.weight            # works for (B, in) and also (B, T, in): matmul uses the last dim
        if self.bias is not None:
            self.out = self.out + self.bias
        return self.out

    def parameters(self):
        return [self.weight] + ([] if self.bias is None else [self.bias])


class BatchNorm1d:
    def __init__(self, dim, eps=1e-5, momentum=0.1):
        self.eps, self.momentum, self.training = eps, momentum, True
        self.gamma, self.beta = torch.ones(dim), torch.zeros(dim)
        self.running_mean, self.running_var = torch.zeros(dim), torch.ones(dim)

    def __call__(self, x):
        if self.training:
            # Average over EVERY dimension except the last (the channels). For (B, T, C) input that is
            # dims (0, 1); the video's "BatchNorm bug" was averaging over dim 0 only.
            dims = tuple(range(x.ndim - 1))
            xmean = x.mean(dims, keepdim=True)
            xvar = x.var(dims, keepdim=True)
        else:
            xmean, xvar = self.running_mean, self.running_var
        xhat = (x - xmean) / torch.sqrt(xvar + self.eps)
        self.out = self.gamma * xhat + self.beta
        if self.training:
            with torch.no_grad():
                self.running_mean = (1 - self.momentum) * self.running_mean + self.momentum * xmean.view(-1)
                self.running_var = (1 - self.momentum) * self.running_var + self.momentum * xvar.view(-1)
        return self.out

    def parameters(self):
        return [self.gamma, self.beta]


class Tanh:
    def __call__(self, x):
        self.out = torch.tanh(x)
        return self.out

    def parameters(self):
        return []


class Embedding:
    def __init__(self, num_embeddings, embedding_dim):
        self.weight = torch.randn((num_embeddings, embedding_dim))

    def __call__(self, IX):
        self.out = self.weight[IX]            # (B, T) integers -> (B, T, C) vectors
        return self.out

    def parameters(self):
        return [self.weight]


class FlattenConsecutive:
    """Glue every n neighbouring vectors together: (B, T, C) -> (B, T/n, C*n)."""

    def __init__(self, n):
        self.n = n

    def __call__(self, x):
        B, T, C = x.shape
        x = x.view(B, T // self.n, C * self.n)
        if x.shape[1] == 1:
            x = x.squeeze(1)                  # (B, 1, C) -> (B, C): drop the length-1 middle dimension
        self.out = x
        return self.out

    def parameters(self):
        return []


class Sequential:
    def __init__(self, layers):
        self.layers = layers

    def __call__(self, x):
        for layer in self.layers:
            x = layer(x)
        self.out = x
        return self.out

    def parameters(self):
        return [p for layer in self.layers for p in layer.parameters()]


def wavenet(vocab, n_embd=24, n_hidden=128):
    return Sequential([
        Embedding(vocab, n_embd),
        FlattenConsecutive(2), Linear(n_embd * 2, n_hidden, bias=False), BatchNorm1d(n_hidden), Tanh(),
        FlattenConsecutive(2), Linear(n_hidden * 2, n_hidden, bias=False), BatchNorm1d(n_hidden), Tanh(),
        FlattenConsecutive(2), Linear(n_hidden * 2, n_hidden, bias=False), BatchNorm1d(n_hidden), Tanh(),
        Linear(n_hidden, vocab),
    ])


def flat_mlp(vocab, block_size, n_embd=10, n_hidden=200):
    """Lesson 08's design, but over 8 characters at once: one big hidden layer."""
    return Sequential([
        Embedding(vocab, n_embd),
        FlattenConsecutive(block_size), Linear(n_embd * block_size, n_hidden, bias=False), BatchNorm1d(n_hidden), Tanh(),
        Linear(n_hidden, vocab),
    ])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--steps", type=int, default=50_000)
    parser.add_argument("--model", choices=["wavenet", "flat"], default="wavenet")
    parser.add_argument("--block-size", type=int, default=8, help="context length; must be a power of 2 for WaveNet")
    args = parser.parse_args()

    words = load_words()
    chars = sorted(set("".join(words)))
    stoi = {s: i + 1 for i, s in enumerate(chars)}
    stoi["."] = 0
    itos = {i: s for s, i in stoi.items()}
    V = len(stoi)

    def build_dataset(ws):
        X, Y = [], []
        for w in ws:
            context = [0] * args.block_size
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
    Xte, Yte = build_dataset(words[n2:])
    print(f"context of {args.block_size} characters | train {tuple(Xtr.shape)} dev {tuple(Xdev.shape)}")

    torch.manual_seed(42)                     # the layers use the global random generator
    model = wavenet(V) if args.model == "wavenet" else flat_mlp(V, args.block_size)
    with torch.no_grad():
        model.layers[-1].weight *= 0.1        # last layer: start unconfident (loss near -ln(1/27))
        for layer in model.layers[:-1]:
            if isinstance(layer, Linear):
                layer.weight *= 5 / 3         # Kaiming gain for tanh
    parameters = model.parameters()
    for p in parameters:
        p.requires_grad = True
    print(f"{args.model}: {sum(p.nelement() for p in parameters):,} parameters")

    # Walk one small batch through the model and print every layer's output shape.
    model(Xtr[:4])
    print("\nshapes for a batch of 4 examples:")
    for layer in model.layers:
        print(f"  {layer.__class__.__name__:<20} -> {tuple(layer.out.shape)}")

    print()
    start, g = time.time(), torch.Generator().manual_seed(2147483647)
    for step in range(args.steps):
        ix = torch.randint(0, Xtr.shape[0], (32,), generator=g)
        loss = F.cross_entropy(model(Xtr[ix]), Ytr[ix])
        for p in parameters:
            p.grad = None
        loss.backward()
        lr = 0.1 if step < args.steps * 3 // 4 else 0.01
        for p in parameters:
            p.data += -lr * p.grad
        if step % (args.steps // 10) == 0:
            print(f"step {step:7d}/{args.steps}  batch loss {loss.item():.4f}  ({time.time() - start:.0f}s)")

    for layer in model.layers:                # evaluation mode: BatchNorm uses its running averages
        if isinstance(layer, BatchNorm1d):
            layer.training = False

    @torch.no_grad()
    def split_loss(X, Y):
        return F.cross_entropy(model(X), Y).item()

    print(f"\ntrain loss {split_loss(Xtr, Ytr):.4f}   dev loss {split_loss(Xdev, Ydev):.4f}"
          f"   (lesson 08 MLP with 3 chars: dev about 2.17)")
    print(f"test loss (checked once, at the end): {split_loss(Xte, Yte):.4f}")

    print("\nnames invented by the model:")
    gs = torch.Generator().manual_seed(2147483647 + 10)
    for _ in range(15):
        out, context = [], [0] * args.block_size
        while True:
            with torch.no_grad():
                probs = F.softmax(model(torch.tensor([context])), dim=1)
            ix = torch.multinomial(probs, num_samples=1, generator=gs).item()
            context = context[1:] + [ix]
            if ix == 0:
                break
            out.append(itos[ix])
        print("  " + "".join(out))


if __name__ == "__main__":
    main()
