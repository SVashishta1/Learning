"""Lesson 05: a neural network that reads handwritten digits, written with numpy only.

Network: 784 pixels -> 128 hidden ReLU neurons -> 10 scores (one per digit 0-9)
Loss:    softmax + cross-entropy (how surprised the model is by the right answer)
Training: mini-batch stochastic gradient descent, every gradient written by hand.

Usage:  python numpy_net.py              (10 epochs, under a minute on a laptop)
        python numpy_net.py --epochs 20  (a little better)
"""
import argparse
import time

import numpy as np

from mnist import load_mnist, show


def init_params(n_in=784, n_hidden=128, n_out=10, seed=0, dtype=np.float32):
    rng = np.random.default_rng(seed)
    return {
        # "He" initialisation: random weights scaled by sqrt(2 / inputs) so signals keep a sensible size.
        "W1": (rng.standard_normal((n_in, n_hidden)) * np.sqrt(2.0 / n_in)).astype(dtype),
        "b1": np.zeros(n_hidden, dtype=dtype),
        # Small output weights -> all 10 scores start near 0 -> the first guess is "10% each".
        "W2": (rng.standard_normal((n_hidden, n_out)) * 0.01).astype(dtype),
        "b2": np.zeros(n_out, dtype=dtype),
    }


def softmax(logits):
    """Turn scores into probabilities that add up to 1 (row by row)."""
    shifted = logits - logits.max(axis=1, keepdims=True)   # subtracting the max avoids exp() overflow; the answer is unchanged
    exps = np.exp(shifted)
    return exps / exps.sum(axis=1, keepdims=True)


def forward(params, X):
    z1 = X @ params["W1"] + params["b1"]        # (B, 784) @ (784, 128) + (128,) -> (B, 128)
    h = np.maximum(z1, 0)                       # ReLU: keep positives, zero out negatives
    logits = h @ params["W2"] + params["b2"]    # (B, 128) @ (128, 10) + (10,) -> (B, 10)
    return logits, (X, z1, h)


def loss_and_grads(params, X, y):
    """Forward pass, cross-entropy loss, and the gradient of the loss for every parameter."""
    B = X.shape[0]
    logits, (X, z1, h) = forward(params, X)
    probs = softmax(logits)
    loss = -np.log(probs[np.arange(B), y] + 1e-12).mean()   # average surprise at the correct digit

    # ---- backward pass (the chain rule, from the loss back to the inputs) ----
    dlogits = probs.copy()
    dlogits[np.arange(B), y] -= 1               # softmax + cross-entropy slope: probs - one_hot(y)
    dlogits /= B                                # because the loss is a MEAN over B examples
    grads = {
        "W2": h.T @ dlogits,                    # (128, B) @ (B, 10) -> (128, 10), same shape as W2
        "b2": dlogits.sum(axis=0),              # the bias was added to every row, so its grads add up
    }
    dh = dlogits @ params["W2"].T               # (B, 10) @ (10, 128) -> (B, 128): blame sent back to h
    dz1 = dh * (z1 > 0)                         # ReLU passes the grad only where it was "on"
    grads["W1"] = X.T @ dz1                     # (784, B) @ (B, 128) -> (784, 128)
    grads["b1"] = dz1.sum(axis=0)
    return loss, grads


def accuracy(params, X, y, batch=10000):
    correct = 0
    for i in range(0, len(X), batch):          # in chunks, to keep memory small
        logits, _ = forward(params, X[i:i + batch])
        correct += (logits.argmax(axis=1) == y[i:i + batch]).sum()
    return correct / len(X)


def gradient_check(seed=1):
    """Compare our hand-written grads with 'nudge and measure' slopes on a tiny random network."""
    rng = np.random.default_rng(seed)
    params = init_params(n_in=6, n_hidden=5, n_out=4, seed=seed, dtype=np.float64)
    params["W2"] = rng.standard_normal((5, 4))  # bigger output weights so every grad is clearly non-zero
    X = rng.standard_normal((3, 6))
    y = np.array([0, 3, 1])
    _, grads = loss_and_grads(params, X, y)
    worst = 0.0
    h = 1e-5
    for name, p in params.items():
        for idx in np.ndindex(p.shape):
            old = p[idx]
            p[idx] = old + h; up, _ = loss_and_grads(params, X, y)
            p[idx] = old - h; down, _ = loss_and_grads(params, X, y)
            p[idx] = old
            numeric = (up - down) / (2 * h)                       # central difference: more accurate
            rel = abs(numeric - grads[name][idx]) / max(1e-8, abs(numeric) + abs(grads[name][idx]))
            worst = max(worst, rel)
    return worst


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--epochs", type=int, default=10)
    parser.add_argument("--lr", type=float, default=0.1)
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument("--hidden", type=int, default=128)
    args = parser.parse_args()

    worst = gradient_check()
    print(f"gradient check: worst relative error {worst:.1e} ->", "OK" if worst < 1e-6 else "PROBLEM!")

    X_train, y_train, X_test, y_test = load_mnist()
    X_val, y_val = X_train[55000:], y_train[55000:]       # hold back 5,000 images to watch progress
    X_train, y_train = X_train[:55000], y_train[:55000]
    print(f"train {len(X_train)}, validation {len(X_val)}, test {len(X_test)} images")

    params = init_params(n_hidden=args.hidden)
    n_params = sum(p.size for p in params.values())
    loss0, _ = loss_and_grads(params, X_train[:1000], y_train[:1000])
    print(f"{n_params:,} parameters | loss before training {loss0:.4f} (a fair 10-way guess gives -ln(1/10) = {np.log(10):.4f})")

    rng = np.random.default_rng(42)
    start = time.time()
    for epoch in range(1, args.epochs + 1):
        order = rng.permutation(len(X_train))              # shuffle so every epoch sees a new order
        losses = []
        for i in range(0, len(order), args.batch_size):
            idx = order[i:i + args.batch_size]
            loss, grads = loss_and_grads(params, X_train[idx], y_train[idx])
            for name in params:
                params[name] -= args.lr * grads[name]      # gradient descent step
            losses.append(loss)
        print(f"epoch {epoch}  train loss {np.mean(losses):.4f}  validation accuracy {accuracy(params, X_val, y_val):.2%}"
              f"  ({time.time() - start:.0f}s)")

    print(f"\nTEST accuracy on 10,000 digits it has never seen: {accuracy(params, X_test, y_test):.2%}")

    logits, _ = forward(params, X_test)
    preds = logits.argmax(axis=1)
    wrong = np.flatnonzero(preds != y_test)
    print(f"it got {len(wrong)} wrong. Here is one of them:")
    i = wrong[0]
    probs = softmax(logits[i:i + 1])[0]
    show(X_test[i])
    print(f"true label {y_test[i]}, model said {preds[i]} ({probs[preds[i]]:.0%} sure); "
          f"it gave the true label {probs[y_test[i]]:.0%}")


if __name__ == "__main__":
    main()
