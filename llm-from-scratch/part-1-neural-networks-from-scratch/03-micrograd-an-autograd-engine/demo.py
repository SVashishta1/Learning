"""Lesson 03 demo: use the micrograd engine step by step, the same way the video does."""
import math

from engine import Value, to_mermaid

print("PART 1: a small expression  L = (a*b + c) * f")
a = Value(2.0, label="a")
b = Value(-3.0, label="b")
c = Value(10.0, label="c")
e = a * b; e.label = "e"
d = e + c; d.label = "d"
f = Value(-2.0, label="f")
L = d * f; L.label = "L"
print(f"forward:  e = a*b = {e.data},  d = e + c = {d.data},  L = d*f = {L.data}")

# Backprop BY HAND, one chain-rule step at a time (from the output back to the inputs).
dL_dL = 1.0                    # L changes 1:1 with itself
dL_dd = f.data * dL_dL         # L = d*f, so dL/dd = f
dL_df = d.data * dL_dL         # ... and dL/df = d
dL_de = 1.0 * dL_dd            # d = e + c: "+" passes the grad through unchanged
dL_dc = 1.0 * dL_dd
dL_da = b.data * dL_de         # e = a*b, so de/da = b, then chain rule: * dL/de
dL_db = a.data * dL_de
print(f"by hand:  dL/da = {dL_da}, dL/db = {dL_db}, dL/dc = {dL_dc}, dL/dd = {dL_dd}, dL/de = {dL_de}, dL/df = {dL_df}")

L.backward()                   # now let the engine do it
print(f"engine:   dL/da = {a.grad}, dL/db = {b.grad}, dL/dc = {c.grad}, dL/dd = {d.grad}, dL/de = {e.grad}, dL/df = {f.grad}")
assert (a.grad, b.grad, c.grad, d.grad, e.grad, f.grad) == (dL_da, dL_db, dL_dc, dL_dd, dL_de, dL_df)
print("match!")

# One tiny "learning" step: move every input in the direction of its grad, so L goes UP.
for v in (a, b, c, f):
    v.data += 0.01 * v.grad
L2 = (a * b + c) * f
print(f"after nudging every input along its grad, L went from -8.0 to {L2.data:.4f} (up, as predicted)")

print("\nPART 2: one neuron  o = tanh(x1*w1 + x2*w2 + b)")
x1 = Value(2.0, label="x1"); x2 = Value(0.0, label="x2")
w1 = Value(-3.0, label="w1"); w2 = Value(1.0, label="w2")
bias = Value(6.8813735870195432, label="b")            # chosen so the numbers come out round
x1w1 = x1 * w1; x1w1.label = "x1*w1"
x2w2 = x2 * w2; x2w2.label = "x2*w2"
s = x1w1 + x2w2; s.label = "x1w1+x2w2"
n = s + bias; n.label = "n"
o = n.tanh(); o.label = "o"
o.backward()
print(f"o = {o.data:.4f}")
for v in (x1, w1, x2, w2, bias, n):
    print(f"  d o / d {v.label:<2} = {v.grad:+.4f}")
print("Notice w2's grad is 0: x2 is 0, so wiggling w2 changes nothing.")

print("\nMermaid picture of this neuron (paste into https://mermaid.live):")
print(to_mermaid(o))

print("\nPART 3: the same neuron, but tanh written as (e^(2n) - 1) / (e^(2n) + 1)")
x1 = Value(2.0); x2 = Value(0.0); w1 = Value(-3.0); w2 = Value(1.0); bias = Value(6.8813735870195432)
n = x1 * w1 + x2 * w2 + bias
e2n = (2 * n).exp()
o = (e2n - 1) / (e2n + 1)
o.backward()
print(f"o = {o.data:.4f};  grads x1 {x1.grad:+.4f}, w1 {w1.grad:+.4f}, x2 {x2.grad:+.4f}, w2 {w2.grad:+.4f}")
print("Same numbers: a big operation or several small ones, the chain rule gives one answer.")

print("\nPART 4: a value used more than once (why grads are ADDED with +=)")
a = Value(3.0, label="a")
b = a + a                       # b = 2a, so db/da must be 2
b.backward()
print(f"b = a + a -> db/da = {a.grad}  (with '=' instead of '+=' it would wrongly be 1.0)")
a = Value(-2.0); b = Value(3.0)
f = (a * b) * (a + b)           # a and b are each used twice
f.backward()
print(f"f = (a*b)*(a+b) at a=-2, b=3 -> df/da = {a.grad}, df/db = {b.grad}")

print("\nPART 5: check against PyTorch")
try:
    import torch

    tx1 = torch.tensor(2.0, dtype=torch.double, requires_grad=True)
    tx2 = torch.tensor(0.0, dtype=torch.double, requires_grad=True)
    tw1 = torch.tensor(-3.0, dtype=torch.double, requires_grad=True)
    tw2 = torch.tensor(1.0, dtype=torch.double, requires_grad=True)
    tb = torch.tensor(6.8813735870195432, dtype=torch.double, requires_grad=True)
    to = torch.tanh(tx1 * tw1 + tx2 * tw2 + tb)
    to.backward()
    print(f"PyTorch:    o = {to.item():.4f}; grads x1 {tx1.grad.item():+.4f}, w1 {tw1.grad.item():+.4f}, "
          f"x2 {tx2.grad.item():+.4f}, w2 {tw2.grad.item():+.4f}")
    print(f"micrograd:  o = {o.data:.4f}; grads x1 {x1.grad:+.4f}, w1 {w1.grad:+.4f}, x2 {x2.grad:+.4f}, w2 {w2.grad:+.4f}")
    same = all(math.isclose(p, q, abs_tol=1e-9) for p, q in
               [(tx1.grad.item(), x1.grad), (tw1.grad.item(), w1.grad), (tx2.grad.item(), x2.grad), (tw2.grad.item(), w2.grad)])
    print("identical!" if same else "DIFFERENT?!")
except ImportError:
    print("(install torch to compare with PyTorch: pip install torch)")
