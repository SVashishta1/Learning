"""Lesson 03: micrograd, a tiny automatic-gradient ("autograd") engine.

A Value is a number that remembers HOW it was made (its parents and the operation).
When you call .backward() on the final answer, every Value in the "family tree"
gets its .grad: how much the final answer would change if this number were nudged up a tiny bit.

This is the same idea as PyTorch's autograd, for single numbers instead of big tensors.
"""
import math


class Value:
    def __init__(self, data, _parents=(), _op="", label=""):
        self.data = float(data)          # the number itself
        self.grad = 0.0                  # d(final output)/d(this number); 0 until backward() runs
        self._backward = lambda: None    # a small function that passes my grad on to my parents
        self._prev = set(_parents)       # the Values this one was made from
        self._op = _op                   # which operation made me ("+", "*", "tanh", ...)
        self.label = label               # an optional name, only for printing

    def __repr__(self):
        name = f"{self.label}=" if self.label else ""
        return f"Value({name}{self.data:.4f}, grad={self.grad:.4f})"

    # ----- the basic operations: each one knows its own LOCAL slope -----
    def __add__(self, other):
        other = other if isinstance(other, Value) else Value(other)   # allow v + 2
        out = Value(self.data + other.data, (self, other), "+")

        def _backward():
            # d(a+b)/da = 1 and d(a+b)/db = 1, so the grad passes straight through.
            # "+=" not "=": a Value used twice must collect blame from BOTH uses.
            self.grad += 1.0 * out.grad
            other.grad += 1.0 * out.grad
        out._backward = _backward
        return out

    def __mul__(self, other):
        other = other if isinstance(other, Value) else Value(other)
        out = Value(self.data * other.data, (self, other), "*")

        def _backward():
            # d(a*b)/da = b and d(a*b)/db = a: each parent gets the OTHER parent's value.
            self.grad += other.data * out.grad
            other.grad += self.data * out.grad
        out._backward = _backward
        return out

    def __pow__(self, k):
        assert isinstance(k, (int, float)), "only plain-number powers, like v**2 or v**-1"
        out = Value(self.data**k, (self,), f"**{k}")

        def _backward():
            self.grad += k * self.data ** (k - 1) * out.grad      # power rule: d(x^k)/dx = k x^(k-1)
        out._backward = _backward
        return out

    def exp(self):
        out = Value(math.exp(self.data), (self,), "exp")

        def _backward():
            self.grad += out.data * out.grad                      # d(e^x)/dx = e^x (it is its own slope)
        out._backward = _backward
        return out

    def log(self):
        out = Value(math.log(self.data), (self,), "log")

        def _backward():
            self.grad += (1.0 / self.data) * out.grad             # d(ln x)/dx = 1/x
        out._backward = _backward
        return out

    def tanh(self):
        t = math.tanh(self.data)
        out = Value(t, (self,), "tanh")

        def _backward():
            self.grad += (1 - t**2) * out.grad                    # d(tanh x)/dx = 1 - tanh(x)^2
        out._backward = _backward
        return out

    def relu(self):
        out = Value(max(0.0, self.data), (self,), "relu")

        def _backward():
            self.grad += (1.0 if out.data > 0 else 0.0) * out.grad  # slope 1 where on, 0 where off
        out._backward = _backward
        return out

    # ----- convenience operations, built from the ones above -----
    def __neg__(self):            # -a
        return self * -1

    def __sub__(self, other):     # a - b
        return self + (-other)

    def __truediv__(self, other):  # a / b  ==  a * b^-1
        return self * (other**-1 if isinstance(other, Value) else Value(other) ** -1)

    def __radd__(self, other):    # 2 + a  (Python tries int.__add__ first, then this)
        return self + other

    def __rsub__(self, other):    # 2 - a
        return Value(other) - self

    def __rmul__(self, other):    # 2 * a
        return self * other

    def __rtruediv__(self, other):  # 2 / a
        return Value(other) / self

    # ----- the magic: backpropagation through the whole family tree -----
    def backward(self):
        # 1. Put every Value in "topological order": a node appears only AFTER all of its parents.
        topo, visited = [], set()

        def build(v):
            if v not in visited:
                visited.add(v)
                for parent in v._prev:
                    build(parent)
                topo.append(v)
        build(self)

        # 2. The output's slope with respect to itself is 1.
        self.grad = 1.0
        # 3. Walk from the output back to the inputs, each node passing its grad to its parents.
        for v in reversed(topo):
            v._backward()


def trace(root):
    """Collect every node and edge in the graph that produced `root`."""
    nodes, edges = set(), set()

    def build(v):
        if v not in nodes:
            nodes.add(v)
            for parent in v._prev:
                edges.add((parent, v))
                build(parent)
    build(root)
    return nodes, edges


def to_mermaid(root):
    """Return the computation graph as Mermaid text (paste it into https://mermaid.live to see it)."""
    nodes, edges = trace(root)
    ordered = sorted(nodes, key=lambda n: (n.label, n.data))   # a fixed order, so the output is repeatable
    ids = {n: f"n{i}" for i, n in enumerate(ordered)}
    lines = ["flowchart LR"]
    for n in ordered:
        name = n.label or "?"
        lines.append(f'    {ids[n]}["{name} | data {n.data:.4f} | grad {n.grad:.4f}"]')
        if n._op:   # an operation bubble between the parents and the result
            lines.append(f'    {ids[n]}_op(("{n._op}")) --> {ids[n]}')
    for parent, child in sorted(edges, key=lambda e: (ids[e[1]], ids[e[0]])):
        lines.append(f"    {ids[parent]} --> {ids[child]}_op")
    return "\n".join(lines)
