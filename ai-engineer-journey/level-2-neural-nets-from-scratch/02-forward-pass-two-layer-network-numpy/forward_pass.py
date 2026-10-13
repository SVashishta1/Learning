"""Project 2.2: push numbers through a 2-layer network by hand with NumPy. No learning yet, just the forward pass.

Network:  2 inputs -> 3 hidden neurons (sigmoid) -> 1 output (sigmoid)
"""
import numpy as np

np.set_printoptions(precision=3, suppress=True)


def sigmoid(z):
    # squashes any number into (0, 1). Big positive -> ~1, big negative -> ~0.
    return 1 / (1 + np.exp(-z))


# ---- 1. ONE neuron, written out longhand ----
x = np.array([1.0, 0.0])          # two input numbers
w = np.array([0.5, -0.4])         # one weight per input: "how much do I care about this input?"
b = 0.1                           # bias: "my default mood"
z = x[0] * w[0] + x[1] * w[1] + b # weighted sum = 0.6
print("one neuron: z =", z, "-> sigmoid(z) =", round(float(sigmoid(z)), 3))

# ---- 2. A whole LAYER of 3 neurons at once = a matrix multiply ----
W1 = np.array([[0.5, -0.3, 0.8],   # shape (2 inputs, 3 neurons): column j = weights of neuron j
               [-0.4, 0.9, 0.2]])
b1 = np.array([0.1, 0.0, -0.2])
W2 = np.array([[0.7], [-1.1], [0.4]])   # shape (3 hidden, 1 output)
b2 = np.array([0.05])

h = sigmoid(x @ W1 + b1)          # @ = matrix multiply. (2,) @ (2,3) -> (3,)
out = sigmoid(h @ W2 + b2)        # (3,) @ (3,1) -> (1,)
print("hidden layer:", h, " output:", out)

# Check neuron 0 by hand matches the matrix version:
assert np.isclose(h[0], sigmoid(1.0 * 0.5 + 0.0 * -0.4 + 0.1))

# ---- 3. A BATCH: run 4 examples at once (rows = examples) ----
X = np.array([[0, 0], [0, 1], [1, 0], [1, 1]], dtype=float)   # shape (4, 2)
H = sigmoid(X @ W1 + b1)          # (4,2) @ (2,3) -> (4,3); b1 is "broadcast" to every row
OUT = sigmoid(H @ W2 + b2)        # (4,3) @ (3,1) -> (4,1)
print("\nshapes: X", X.shape, "-> H", H.shape, "-> OUT", OUT.shape)
for xi, oi in zip(X, OUT):
    print(f"input {xi} -> output {oi[0]:.3f}")
print("\nThese outputs are random-ish because the weights are made up. In 2.3 we LEARN the weights.")
