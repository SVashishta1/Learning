"""Project 2.4: 'tinyframe', a mini deep-learning framework in ~80 lines.

Same math as 2.3, but organised like PyTorch: every layer knows how to go
FORWARD (compute output) and BACKWARD (pass blame to its inputs and store gradients for its own weights).
"""
import numpy as np


class Layer:
    params: list = []
    def forward(self, x): raise NotImplementedError
    def backward(self, grad): raise NotImplementedError


class Linear(Layer):
    def __init__(self, n_in, n_out, rng):
        # "He/Xavier-style" init: scale random weights so signals don't explode or vanish
        self.W = rng.normal(0, np.sqrt(2 / (n_in + n_out)), (n_in, n_out))
        self.b = np.zeros(n_out)
        self.params = [self.W, self.b]

    def forward(self, x):
        self.x = x                     # remember input: backward needs it
        return x @ self.W + self.b

    def backward(self, grad):
        self.grads = [self.x.T @ grad, grad.sum(axis=0)]   # dW, db
        return grad @ self.W.T                             # blame for the previous layer


class ReLU(Layer):
    def forward(self, x):
        self.mask = x > 0
        return x * self.mask
    def backward(self, grad):
        return grad * self.mask        # no gradient where the neuron was "off"


class Tanh(Layer):
    def forward(self, x):
        self.out = np.tanh(x)
        return self.out
    def backward(self, grad):
        return grad * (1 - self.out ** 2)


class Sigmoid(Layer):
    def forward(self, x):
        self.out = 1 / (1 + np.exp(-x))
        return self.out
    def backward(self, grad):
        return grad * self.out * (1 - self.out)


class Sequential:
    def __init__(self, *layers): self.layers = layers
    def __call__(self, x):
        for layer in self.layers:
            x = layer.forward(x)
        return x
    def backward(self, grad):
        for layer in reversed(self.layers):
            grad = layer.backward(grad)
    def step(self, lr):                # SGD optimizer: nudge every parameter downhill
        for layer in self.layers:
            for p, g in zip(layer.params, getattr(layer, "grads", [])):
                p -= lr * g


def bce_loss(p, y):
    """Binary cross-entropy: the standard loss for yes/no problems. Returns (loss, gradient)."""
    p = np.clip(p, 1e-7, 1 - 1e-7)
    loss = -np.mean(y * np.log(p) + (1 - y) * np.log(1 - p))
    grad = (p - y) / (p * (1 - p)) / len(y)
    return loss, grad
