"""Project 2.3: teach a 2-layer network XOR by computing every gradient BY HAND (chain rule).

XOR: output is 1 when exactly one input is 1.   (0,0)->0  (0,1)->1  (1,0)->1  (1,1)->0
A single neuron CAN'T learn this (it's not a straight-line split). A hidden layer can.
"""
import numpy as np

rng = np.random.default_rng(42)
X = np.array([[0, 0], [0, 1], [1, 0], [1, 1]], dtype=float)
Y = np.array([[0], [1], [1], [0]], dtype=float)

sigmoid = lambda z: 1 / (1 + np.exp(-z))

# Random small starting weights
W1, b1 = rng.normal(0, 1, (2, 4)), np.zeros(4)   # 2 inputs -> 4 hidden
W2, b2 = rng.normal(0, 1, (4, 1)), np.zeros(1)   # 4 hidden -> 1 output


def forward(X, W1, b1, W2, b2):
    z1 = X @ W1 + b1
    h = sigmoid(z1)
    z2 = h @ W2 + b2
    p = sigmoid(z2)
    return z1, h, z2, p


def loss_fn(p, Y):
    return np.mean((p - Y) ** 2)


def backward(X, Y, h, p, W2):
    """The chain rule, one link at a time. Read it bottom-up from the loss."""
    n = len(X)
    dp = 2 * (p - Y) / n              # d loss / d p          (from mean squared error)
    dz2 = dp * p * (1 - p)            # d loss / d z2         (sigmoid'(z) = s * (1 - s))
    dW2 = h.T @ dz2                   # d loss / d W2         (z2 = h @ W2)
    db2 = dz2.sum(axis=0)
    dh = dz2 @ W2.T                   # d loss / d h          (blame flows back to the hidden layer)
    dz1 = dh * h * (1 - h)
    dW1 = X.T @ dz1
    db1 = dz1.sum(axis=0)
    return dW1, db1, dW2, db2


# ---- Gradient check: compare our calculus with the "nudge" method from 2.1 ----
_, h, _, p = forward(X, W1, b1, W2, b2)
dW1, *_ = backward(X, Y, h, p, W2)
eps = 1e-6
W1_plus = W1.copy(); W1_plus[0, 0] += eps
numeric = (loss_fn(forward(X, W1_plus, b1, W2, b2)[3], Y) - loss_fn(p, Y)) / eps
print(f"gradient check W1[0,0]: by hand {dW1[0, 0]:.6f} vs nudge {numeric:.6f}")
assert abs(dW1[0, 0] - numeric) < 1e-4, "backprop has a bug!"

# ---- Training loop ----
lr = 2.0
for epoch in range(1, 5001):
    z1, h, z2, p = forward(X, W1, b1, W2, b2)
    dW1, db1, dW2, db2 = backward(X, Y, h, p, W2)
    W1 -= lr * dW1; b1 -= lr * db1
    W2 -= lr * dW2; b2 -= lr * db2
    if epoch in (1, 100, 500, 1000, 2500, 5000):
        print(f"epoch {epoch:5d} | loss {loss_fn(p, Y):.5f}")

p = forward(X, W1, b1, W2, b2)[3]
print("\nXOR learned:")
for xi, pi, yi in zip(X.astype(int), p.ravel(), Y.ravel()):
    print(f"  {xi} -> {pi:.3f}  (want {int(yi)}) {'✅' if round(pi) == yi else '❌'}")
