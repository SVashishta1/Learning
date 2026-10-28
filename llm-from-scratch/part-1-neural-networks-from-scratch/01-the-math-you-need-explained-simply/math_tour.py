"""Lesson 01: the maths you need for neural networks, explained with tiny numbers.

Run it and read the output next to the README. Every section prints a small
experiment so you can SEE the idea instead of memorising a formula.
"""
import math

import numpy as np


def section(title):
    print("\n" + "=" * 60)
    print(title)
    print("=" * 60)


# ---------------------------------------------------------------------------
# 1. A DERIVATIVE IS A SLOPE: "if I nudge x a tiny bit, how much does f(x) move?"
# ---------------------------------------------------------------------------
section("1. Derivative = slope (nudge x, watch f move)")


def f(x):
    return 3 * x**2 - 4 * x + 5          # a simple curved function (a "parabola")


x = 3.0
print(f"f({x}) = {f(x)}")
for h in [1.0, 0.1, 0.01, 0.001, 0.0001]:
    slope = (f(x + h) - f(x)) / h        # rise / run: how much f moved, divided by the nudge
    print(f"nudge h = {h:<7} -> f moved by {f(x + h) - f(x):10.6f} -> slope = {slope:.4f}")
print("exact slope from the rule 6x - 4 =", 6 * x - 4)
print("At x = -3 the slope is", round((f(-3 + 1e-6) - f(-3)) / 1e-6, 3), "(negative: f goes DOWN as x goes up)")
print("At x = 2/3 the slope is", round((f(2 / 3 + 1e-6) - f(2 / 3)) / 1e-6, 3), "(zero: the bottom of the valley)")

# ---------------------------------------------------------------------------
# 2. MANY INPUTS -> one slope per input ("partial derivatives")
# ---------------------------------------------------------------------------
section("2. Several inputs: one slope for each (partial derivatives)")
a, b, c = 2.0, -3.0, 10.0
d = a * b + c
h = 0.0001
print(f"d = a*b + c = {a}*{b} + {c} = {d}")
print(f"nudge a: slope = {((a + h) * b + c - d) / h:.4f}   (rule says: b = {b})")
print(f"nudge b: slope = {(a * (b + h) + c - d) / h:.4f}   (rule says: a = {a})")
print(f"nudge c: slope = {(a * b + (c + h) - d) / h:.4f}   (rule says: 1)")

# ---------------------------------------------------------------------------
# 3. THE CHAIN RULE: slopes MULTIPLY along a chain
# ---------------------------------------------------------------------------
section("3. Chain rule: slopes multiply along a chain")
# y = (2x + 1)^2 is two steps: u = 2x + 1, then y = u^2
x = 1.0
u = 2 * x + 1                            # step 1
y = u**2                                 # step 2
du_dx = 2.0                              # u grows 2 for each 1 that x grows
dy_du = 2 * u                            # y = u^2 has slope 2u
print(f"x = {x}, u = 2x+1 = {u}, y = u^2 = {y}")
print(f"du/dx = {du_dx}, dy/du = 2u = {dy_du}")
print(f"chain rule: dy/dx = dy/du * du/dx = {dy_du} * {du_dx} = {dy_du * du_dx}")
numeric = (((2 * (x + h) + 1) ** 2) - y) / h
print(f"check by nudging x: {numeric:.4f}")

# ---------------------------------------------------------------------------
# 4. GRADIENT DESCENT: walk downhill by following the slope
# ---------------------------------------------------------------------------
section("4. Gradient descent: walk downhill to the lowest point")


def loss(w):
    return (w - 3) ** 2                  # lowest (0) when w = 3


w = 0.0
learning_rate = 0.1                      # how big each downhill step is
for step in range(31):
    slope = 2 * (w - 3)                  # derivative of (w - 3)^2
    if step % 5 == 0:
        print(f"step {step:2d}: w = {w:.4f}  loss = {loss(w):.6f}  slope = {slope:+.4f}")
    w = w - learning_rate * slope        # step AGAINST the slope (downhill)
print("w ends close to 3, where the loss is smallest.")

# ---------------------------------------------------------------------------
# 5. VECTORS: lists of numbers; the DOT PRODUCT is "multiply pairs, add up"
# ---------------------------------------------------------------------------
section("5. Vectors and the dot product (a shopping receipt)")
quantities = np.array([2, 1, 3])         # 2 apples, 1 bread, 3 milks
prices = np.array([0.5, 2.0, 1.2])       # price of each
print("quantities =", quantities, " prices =", prices)
print("element by element:", quantities * prices)
print("dot product (the total bill) =", quantities @ prices, "=", np.dot(quantities, prices))
print("shape of a vector:", quantities.shape)

# ---------------------------------------------------------------------------
# 6. MATRICES: a table of numbers; matrix @ vector = many dot products at once
# ---------------------------------------------------------------------------
section("6. Matrices: many dot products at once (a layer of neurons)")
x = np.array([1.0, 2.0])                 # 2 inputs
W = np.array([[0.1, 0.2],                # neuron 1's two weights
              [0.3, -0.4],               # neuron 2's two weights
              [0.5, 0.6]])               # neuron 3's two weights
print("W has shape", W.shape, "(3 rows = 3 neurons, 2 columns = 2 inputs)")
print("W @ x =", W @ x, "  <- each row dotted with x")
print("row by row:", [float(W[i] @ x) for i in range(3)])

X = np.array([[1.0, 2.0],                # a BATCH: 4 examples, each with 2 inputs
              [0.0, 1.0],
              [-1.0, 3.0],
              [2.0, 2.0]])
out = X @ W.T                            # (4, 2) @ (2, 3) -> (4, 3): 3 neuron outputs per example
print("X shape", X.shape, "@ W.T shape", W.T.shape, "->", out.shape)
print(out)

# ---------------------------------------------------------------------------
# 7. BROADCASTING: numpy stretches a smaller array to fit a bigger one
# ---------------------------------------------------------------------------
section("7. Broadcasting: add one bias row to every example")
bias = np.array([1.0, 0.0, -1.0])        # one bias per neuron, shape (3,)
print("out shape", out.shape, "+ bias shape", bias.shape, "->", (out + bias).shape)
print(out + bias)

# ---------------------------------------------------------------------------
# 8. SUMS, MEANS AND SPREAD along an axis
# ---------------------------------------------------------------------------
section("8. Sum / mean / standard deviation along an axis")
print("sum of everything:", out.sum())
print("sum down each column (axis=0):", out.sum(axis=0))
print("sum across each row (axis=1):", out.sum(axis=1))
print("keepdims keeps the shape (4, 1):", out.sum(axis=1, keepdims=True).shape)
numbers = np.array([2.0, 4.0, 4.0, 4.0, 5.0, 5.0, 7.0, 9.0])
print("numbers:", numbers, " mean:", numbers.mean(), " std:", numbers.std())

# ---------------------------------------------------------------------------
# 9. EXP and LOG: the two functions behind probabilities and "loss"
# ---------------------------------------------------------------------------
section("9. exp turns any number positive; log measures surprise")
for z in [-2, 0, 1, 2]:
    print(f"exp({z:2d}) = {math.exp(z):8.4f}")
print("log undoes exp: log(exp(2)) =", math.log(math.exp(2)))
print("log turns multiply into add: log(0.5*0.2) =", round(math.log(0.5 * 0.2), 4),
      "= log(0.5)+log(0.2) =", round(math.log(0.5) + math.log(0.2), 4))
print("\nSurprise = -log(probability you gave the right answer):")
for p in [1.0, 0.9, 0.5, 0.1, 0.01]:
    print(f"  p = {p:<5} -> -log(p) = {abs(math.log(p)):.4f}")   # abs() avoids printing "-0.0000"

scores = np.array([2.0, 1.0, 0.1])       # raw scores for 3 choices
probs = np.exp(scores) / np.exp(scores).sum()
print("\nsoftmax preview: scores", scores, "-> probabilities", probs.round(4), "sum =", probs.sum())

print("\nDone! You have now used every maths idea the rest of the course needs.")
