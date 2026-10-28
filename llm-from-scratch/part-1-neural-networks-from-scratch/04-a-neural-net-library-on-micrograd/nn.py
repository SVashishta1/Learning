"""Lesson 04: a tiny neural-network library built on the micrograd engine.

Neuron -> Layer (many neurons side by side) -> MLP (layers one after another).
Every class can list its parameters() (the knobs that training adjusts),
which is exactly how PyTorch's nn.Module is organised.
"""
import random

from engine import Value


class Module:
    """Shared behaviour for everything that has parameters."""

    def zero_grad(self):
        # Grads ADD UP (+=) in the engine, so wipe them before every backward pass.
        for p in self.parameters():
            p.grad = 0.0

    def parameters(self):
        return []


class Neuron(Module):
    def __init__(self, n_inputs, activation="tanh"):
        # One weight per input, random between -1 and 1, plus one bias that starts at 0.
        self.w = [Value(random.uniform(-1, 1)) for _ in range(n_inputs)]
        self.b = Value(0.0)
        self.activation = activation      # "tanh", "relu" or None (None = plain, "linear")

    def __call__(self, x):
        # sum(w_i * x_i) + b, starting the sum from b so we don't need an extra "+ b"
        act = sum((wi * xi for wi, xi in zip(self.w, x)), self.b)
        if self.activation == "tanh":
            return act.tanh()
        if self.activation == "relu":
            return act.relu()
        return act

    def parameters(self):
        return self.w + [self.b]

    def __repr__(self):
        return f"{self.activation or 'linear'}Neuron({len(self.w)})"


class Layer(Module):
    def __init__(self, n_inputs, n_outputs, **kwargs):
        self.neurons = [Neuron(n_inputs, **kwargs) for _ in range(n_outputs)]

    def __call__(self, x):
        outs = [n(x) for n in self.neurons]          # every neuron looks at the SAME inputs
        return outs[0] if len(outs) == 1 else outs   # a single output is returned as a Value, not a list

    def parameters(self):
        return [p for n in self.neurons for p in n.parameters()]

    def __repr__(self):
        return f"Layer of [{', '.join(str(n) for n in self.neurons)}]"


class MLP(Module):
    """Multi-Layer Perceptron: layers in a chain. MLP(3, [4, 4, 1]) = 3 inputs -> 4 -> 4 -> 1 output."""

    def __init__(self, n_inputs, layer_sizes, activation="tanh", last_activation=None):
        sizes = [n_inputs] + layer_sizes
        self.layers = []
        for i in range(len(layer_sizes)):
            is_last = i == len(layer_sizes) - 1
            act = last_activation if is_last else activation
            self.layers.append(Layer(sizes[i], sizes[i + 1], activation=act))

    def __call__(self, x):
        for layer in self.layers:
            x = layer(x)                              # the output of one layer is the input of the next
        return x

    def parameters(self):
        return [p for layer in self.layers for p in layer.parameters()]

    def __repr__(self):
        return f"MLP of [{', '.join(str(layer) for layer in self.layers)}]"
