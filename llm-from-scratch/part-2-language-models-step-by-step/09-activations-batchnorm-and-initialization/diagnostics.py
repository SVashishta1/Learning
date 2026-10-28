"""Lesson 09, part 2: a DEEP network (5 hidden layers) and the health checks professionals use.

We write our own Linear, BatchNorm1d and Tanh layers (same names and behaviour as torch.nn),
build a 6-layer MLP, train it briefly, and print for every layer:
  - forward:  mean, std and % saturated of the tanh outputs (are signals dying or exploding?)
  - backward: std of the gradients flowing into each layer (do all layers learn?)
  - weights:  grad:data ratio, and the update:data ratio (about 1e-3 is healthy)

Three experiments: good gain (5/3), too-small gain (0.5), and BatchNorm.
Usage:  python diagnostics.py                (about a minute)
        python diagnostics.py --steps 3000   (longer runs)
"""
import argparse
import math

import torch
import torch.nn.functional as F

from names_data import load_words

torch.set_num_threads(1)


class Linear:
    def __init__(self, fan_in, fan_out, gain, bias=True, g=None):
        self.weight = torch.randn((fan_in, fan_out), generator=g) * gain / math.sqrt(fan_in)
        self.bias = torch.zeros(fan_out) if bias else None

    def __call__(self, x):
        self.out = x @ self.weight
        if self.bias is not None:
            self.out = self.out + self.bias
        return self.out

    def parameters(self):
        return [self.weight] + ([] if self.bias is None else [self.bias])


class BatchNorm1d:
    def __init__(self, dim, eps=1e-5, momentum=0.1):
        self.eps, self.momentum, self.training = eps, momentum, True
        self.gamma, self.beta = torch.ones(dim), torch.zeros(dim)              # trained by backprop
        self.running_mean, self.running_var = torch.zeros(dim), torch.ones(dim)  # updated by averaging

    def __call__(self, x):
        if self.training:
            xmean, xvar = x.mean(0, keepdim=True), x.var(0, keepdim=True)
        else:
            xmean, xvar = self.running_mean, self.running_var
        xhat = (x - xmean) / torch.sqrt(xvar + self.eps)       # mean 0, variance 1
        self.out = self.gamma * xhat + self.beta
        if self.training:
            with torch.no_grad():
                self.running_mean = (1 - self.momentum) * self.running_mean + self.momentum * xmean
                self.running_var = (1 - self.momentum) * self.running_var + self.momentum * xvar
        return self.out

    def parameters(self):
        return [self.gamma, self.beta]


class Tanh:
    def __call__(self, x):
        self.out = torch.tanh(x)
        return self.out

    def parameters(self):
        return []


def build(gain, batchnorm, n_embd=10, n_hidden=100, block=3, vocab=27, seed=2147483647):
    g = torch.Generator().manual_seed(seed)
    C = torch.randn((vocab, n_embd), generator=g)
    sizes = [n_embd * block] + [n_hidden] * 5
    layers = []
    for a, b in zip(sizes, sizes[1:]):
        layers.append(Linear(a, b, gain, bias=not batchnorm, g=g))   # BatchNorm has its own shift, so no bias
        if batchnorm:
            layers.append(BatchNorm1d(b))
        layers.append(Tanh())
    layers.append(Linear(n_hidden, vocab, gain=1.0, bias=True, g=g))
    if batchnorm:
        layers.append(BatchNorm1d(vocab))
    with torch.no_grad():                                 # make the very first predictions unconfident
        if batchnorm:
            layers[-1].gamma *= 0.1
        else:
            layers[-1].weight *= 0.1
    params = [C] + [p for layer in layers for p in layer.parameters()]
    for p in params:
        p.requires_grad = True
    return C, layers, params


def dataset():
    words = load_words()
    chars = sorted(set("".join(words)))
    stoi = {s: i + 1 for i, s in enumerate(chars)}
    stoi["."] = 0
    X, Y = [], []
    for w in words:
        context = [0] * 3
        for ch in w + ".":
            X.append(context)
            Y.append(stoi[ch])
            context = context[1:] + [stoi[ch]]
    return torch.tensor(X), torch.tensor(Y)


def health_report(layers):
    """Forward and backward statistics of every Tanh layer (call right after loss.backward())."""
    print(f"{'layer':<10} {'out mean':>9} {'out std':>8} {'saturated':>10} {'grad std':>10}")
    for i, layer in enumerate(layers[:-1]):
        if isinstance(layer, Tanh):
            t = layer.out
            print(f"{i:>2} Tanh    {t.mean().item():+9.2f} {t.std().item():8.2f} {(t.abs() > 0.97).float().mean().item():10.2%}"
                  f" {t.grad.std().item():10.2e}")


def experiment(name, gain, batchnorm, X, Y, steps):
    C, layers, params = build(gain, batchnorm)
    g = torch.Generator().manual_seed(42)
    ud, losses = [], []                                   # update:data ratios and losses, one entry per step
    lr = 0.1
    print(f"\n=== {name} ===")
    for step in range(steps):
        ix = torch.randint(0, X.shape[0], (32,), generator=g)
        x = C[X[ix]].view(32, -1)
        for layer in layers:
            x = layer(x)
        loss = F.cross_entropy(x, Y[ix])
        for layer in layers:
            layer.out.retain_grad()                        # keep the grads of every layer's output for inspection
        for p in params:
            p.grad = None
        loss.backward()
        if step == 0:
            print("health at initialisation (first batch):")
            health_report(layers)
        for p in params:
            p.data += -lr * p.grad
        with torch.no_grad():
            ud.append([((lr * p.grad).std() / p.data.std()).log10().item() for p in params if p.ndim == 2])
        losses.append(loss.item())

    last = ud[-100:]
    avg_ud = [sum(col) / len(col) for col in zip(*last)]
    print(f"after {steps} steps: average batch loss over the last 100 steps {sum(losses[-100:]) / 100:.4f}")
    print(f"{'weight shape':<14} {'grad:data':>10} {'log10 update:data (avg of last 100 steps)':>43}")
    weights = [p for p in params if p.ndim == 2]
    for p, r in zip(weights, avg_ud):
        print(f"{str(tuple(p.shape)):<14} {(p.grad.std() / p.data.std()).item():10.2e} {r:43.2f}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--steps", type=int, default=1000)
    args = parser.parse_args()
    X, Y = dataset()
    experiment("Tanh layers, gain 5/3 (Kaiming), no BatchNorm", 5 / 3, False, X, Y, args.steps)
    experiment("Tanh layers, gain 0.5 (too small), no BatchNorm", 0.5, False, X, Y, args.steps)
    experiment("Tanh layers, gain 0.5 (too small), WITH BatchNorm", 0.5, True, X, Y, args.steps)
    print("\nRead it like a doctor: with gain 0.5 and no BatchNorm the signal SHRINKS layer after layer at the")
    print("start (out std falls, gradients are uneven) and the loss ends higher. BatchNorm re-normalises every")
    print("layer, so even the bad gain trains well. Rule of thumb from the video: log10 update:data around -3")
    print("(each step changes a weight by ~0.1% of its size). Here most are -2 to -2.5: lr 0.1 is on the fast")
    print("side, fine for a short run. Much higher (-1) = steps too big; much lower (-4) = learning too slowly.")
