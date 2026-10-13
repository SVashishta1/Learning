"""1) Backprop through a tiny expression and check by hand. 2) Train an MLP. 3) Cross-check with PyTorch."""
import random

from engine import Value
from nn import MLP

# ---- 1. A tiny expression: L = (a*b + c) * f ----
a, b, c, f = Value(2.0, label="a"), Value(-3.0, label="b"), Value(10.0, label="c"), Value(-2.0, label="f")
e = a * b; e.label = "e"
d = e + c; d.label = "d"
L = d * f; L.label = "L"
L.backward()
print("L =", L.data)
print(a, b, c, f, sep="\n")
# By hand: dL/da = dL/dd * dd/de * de/da = f * 1 * b = -2 * -3 = 6
assert a.grad == 6.0 and b.grad == -4.0 and c.grad == -2.0 and f.grad == 4.0
print("✅ hand-calculated gradients match\n")

# ---- 2. Train a tiny MLP (3 -> 4 -> 4 -> 1) on 4 examples ----
random.seed(1337)
xs = [[2.0, 3.0, -1.0], [3.0, -1.0, 0.5], [0.5, 1.0, 1.0], [1.0, 1.0, -1.0]]
ys = [1.0, -1.0, -1.0, 1.0]
model = MLP(3, [4, 4, 1])
print(f"model has {len(model.parameters())} parameters")
for step in range(1, 101):
    preds = [model(x) for x in xs]
    loss = sum((p - y) ** 2 for p, y in zip(preds, ys))
    for p in model.parameters():
        p.grad = 0.0                     # zero_grad (same reason as PyTorch)
    loss.backward()
    for p in model.parameters():
        p.data -= 0.05 * p.grad          # SGD step
    if step in (1, 10, 50, 100):
        print(f"step {step:3d} | loss {loss.data:.5f}")
print("predictions:", [round(model(x).data, 3) for x in xs], "targets:", ys)

# ---- 3. Optional: same expression in PyTorch ----
try:
    import torch
    x = torch.tensor(-4.0, dtype=torch.double, requires_grad=True)
    z = (2 * x + 2 + x).relu() + (x * x).relu() * 3
    z.backward()
    xv = Value(-4.0)
    zv = (2 * xv + 2 + xv).relu() + (xv * xv).relu() * 3
    zv.backward()
    print(f"\nPyTorch dz/dx = {x.grad.item()}  | micrograd dz/dx = {xv.grad}")
    assert abs(x.grad.item() - xv.grad) < 1e-9
    print("✅ micrograd agrees with PyTorch")
except ImportError:
    print("\n(install torch to cross-check against PyTorch)")
