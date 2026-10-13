"""Project 2.6: a scalar autograd engine (after Karpathy's micrograd).

A `Value` is a number that REMEMBERS how it was made (its parents and the operation).
Calling .backward() walks that family tree in reverse and fills in .grad for every Value.
"""
import math


class Value:
    def __init__(self, data, _parents=(), _op="", label=""):
        self.data = float(data)
        self.grad = 0.0                 # d(final output) / d(this value)
        self._backward = lambda: None   # how to push my grad into my parents
        self._parents = set(_parents)
        self._op = _op
        self.label = label

    def __repr__(self):
        return f"Value({self.label + '=' if self.label else ''}{self.data:.4f}, grad={self.grad:.4f})"

    # ---- operations: each one defines its local derivative ----
    def __add__(self, other):
        other = other if isinstance(other, Value) else Value(other)
        out = Value(self.data + other.data, (self, other), "+")
        def _backward():                # d(a+b)/da = 1, d(a+b)/db = 1
            self.grad += out.grad
            other.grad += out.grad
        out._backward = _backward
        return out

    def __mul__(self, other):
        other = other if isinstance(other, Value) else Value(other)
        out = Value(self.data * other.data, (self, other), "*")
        def _backward():                # d(a*b)/da = b, d(a*b)/db = a
            self.grad += other.data * out.grad
            other.grad += self.data * out.grad
        out._backward = _backward
        return out

    def __pow__(self, k):
        out = Value(self.data ** k, (self,), f"**{k}")
        def _backward():
            self.grad += k * self.data ** (k - 1) * out.grad
        out._backward = _backward
        return out

    def tanh(self):
        t = math.tanh(self.data)
        out = Value(t, (self,), "tanh")
        def _backward():
            self.grad += (1 - t ** 2) * out.grad
        out._backward = _backward
        return out

    def relu(self):
        out = Value(max(0.0, self.data), (self,), "relu")
        def _backward():
            self.grad += (out.data > 0) * out.grad
        out._backward = _backward
        return out

    # convenience so we can write natural math
    def __neg__(self): return self * -1
    def __sub__(self, other): return self + (-other)
    def __radd__(self, other): return self + other
    def __rmul__(self, other): return self * other
    def __rsub__(self, other): return Value(other) - self
    def __truediv__(self, other): return self * (other ** -1 if isinstance(other, Value) else 1 / other)

    def backward(self):
        # 1. topological sort: make sure we process a node only after everything that USES it
        order, seen = [], set()
        def build(v):
            if v not in seen:
                seen.add(v)
                for p in v._parents:
                    build(p)
                order.append(v)
        build(self)
        # 2. the output's gradient with respect to itself is 1; then apply the chain rule backwards
        self.grad = 1.0
        for v in reversed(order):
            v._backward()
