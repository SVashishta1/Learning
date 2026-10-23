"""Lesson 02: one artificial neuron in plain Python (no libraries at all).

A neuron takes some numbers in, multiplies each by a weight, adds a bias,
and squashes the result with an "activation function". We will:
  1. run a neuron by hand on one example,
  2. work out its gradients with the chain rule,
  3. check those gradients by nudging (a "gradient check"),
  4. train it to learn the AND and OR gates,
  5. watch it FAIL on XOR (and learn why we need more neurons).
"""
import math
import random


def sigmoid(z):
    """Squash any number into the range 0..1 (a 'probability-like' number)."""
    return 1.0 / (1.0 + math.exp(-z))


def neuron(x, w, b):
    """x and w are lists of the same length. Returns (z, p): the raw sum and the squashed output."""
    z = sum(wi * xi for wi, xi in zip(w, x)) + b   # weighted sum + bias
    return z, sigmoid(z)


def loss_and_grads(data, w, b):
    """Mean squared error over all examples, plus d(loss)/d(each weight) and d(loss)/d(bias).

    For ONE example the chain is:  w, b -> z -> p -> L = (p - y)^2
      dL/dp = 2 (p - y)          (slope of a square)
      dp/dz = p (1 - p)          (slope of the sigmoid)
      dz/dw_i = x_i, dz/db = 1   (slope of a weighted sum)
    Multiply along the chain, then average over the examples.
    """
    n = len(data)
    total = 0.0
    dw = [0.0] * len(w)
    db = 0.0
    for x, y in data:
        z, p = neuron(x, w, b)
        total += (p - y) ** 2
        dL_dz = 2 * (p - y) * p * (1 - p)           # chain rule: dL/dp * dp/dz
        for i in range(len(w)):
            dw[i] += dL_dz * x[i] / n               # * dz/dw_i, averaged
        db += dL_dz * 1.0 / n                       # * dz/db, averaged
    return total / n, dw, db


def numeric_grads(data, w, b, h=1e-6):
    """Estimate the same gradients by nudging each knob a tiny bit (slow but simple)."""
    base, _, _ = loss_and_grads(data, w, b)
    dw = []
    for i in range(len(w)):
        w2 = list(w)
        w2[i] += h
        dw.append((loss_and_grads(data, w2, b)[0] - base) / h)
    db = (loss_and_grads(data, w, b + h)[0] - base) / h
    return dw, db


def train(data, steps=3000, lr=2.0, seed=0, report_every=1000):
    random.seed(seed)
    w = [random.uniform(-1, 1) for _ in range(len(data[0][0]))]
    b = 0.0
    for step in range(steps + 1):
        loss, dw, db = loss_and_grads(data, w, b)
        if step % report_every == 0:
            print(f"  step {step:5d}  loss {loss:.5f}")
        w = [wi - lr * dwi for wi, dwi in zip(w, dw)]   # gradient descent: step downhill
        b = b - lr * db
    return w, b


AND = [([0, 0], 0), ([0, 1], 0), ([1, 0], 0), ([1, 1], 1)]
OR = [([0, 0], 0), ([0, 1], 1), ([1, 0], 1), ([1, 1], 1)]
XOR = [([0, 0], 0), ([0, 1], 1), ([1, 0], 1), ([1, 1], 0)]

if __name__ == "__main__":
    print("1) One forward pass by hand")
    x, w, b = [2.0, 3.0], [0.5, -1.0], 1.0
    z, p = neuron(x, w, b)
    print(f"  z = 0.5*2 + (-1.0)*3 + 1 = {z}")
    print(f"  p = sigmoid({z}) = {p:.4f}")

    print("\n2) Gradients by the chain rule vs by nudging (gradient check)")
    w0, b0 = [0.3, -0.2], 0.1
    loss, dw, db = loss_and_grads(AND, w0, b0)
    ndw, ndb = numeric_grads(AND, w0, b0)
    print(f"  loss = {loss:.6f}")
    for i in range(2):
        print(f"  dL/dw{i + 1}: chain rule {dw[i]:+.6f}   nudging {ndw[i]:+.6f}")
    print(f"  dL/db : chain rule {db:+.6f}   nudging {ndb:+.6f}")
    worst = max(abs(a - b) for a, b in zip(dw + [db], ndw + [ndb]))
    print(f"  biggest difference: {worst:.1e}  ->", "OK, they agree" if worst < 1e-5 else "MISMATCH!")

    for number, (name, data) in enumerate([("AND", AND), ("OR", OR), ("XOR", XOR)], start=3):
        print(f"\n{number}) Learning {name}")
        w, b = train(data)
        tidy = lambda v: f"{v:.2f}".replace("-0.00", "0.00")   # don't print "-0.00"
        print(f"  learned w = [{tidy(w[0])}, {tidy(w[1])}], b = {tidy(b)}")
        for x, y in data:
            p = neuron(x, w, b)[1]
            if abs(p - 0.5) < 0.05:
                verdict = "can't decide (coin flip)"
            else:
                verdict = "right" if (p > 0.5) == (y == 1) else "WRONG"
            print(f"  {x} -> {p:.3f} (target {y}) {verdict}")

    print("\nOne neuron draws ONE straight line. AND and OR can be split by a line;")
    print("XOR cannot, so the neuron gets stuck near 0.5. Lesson 04 fixes this with layers.")
