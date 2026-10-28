"""Run with:  pytest -q"""
import random

from engine import Value
from nn import MLP, Layer, Neuron
from train_moons import make_moons


def test_parameter_counts():
    assert len(Neuron(3).parameters()) == 4                 # 3 weights + 1 bias
    assert len(Layer(3, 4).parameters()) == 16              # 4 neurons x 4
    assert len(MLP(3, [4, 4, 1]).parameters()) == 41        # 16 + 20 + 5


def test_zero_grad_clears_everything():
    model = MLP(2, [3, 1])
    model([1.0, 2.0]).backward()
    assert any(p.grad != 0 for p in model.parameters())
    model.zero_grad()
    assert all(p.grad == 0 for p in model.parameters())


def test_gradient_check_whole_network():
    # Nudge each parameter and compare the change in the loss with its .grad.
    random.seed(0)
    model = MLP(2, [3, 1], activation="tanh", last_activation="tanh")
    x, y = [0.5, -1.0], 1.0

    def loss():
        return (model(x) - y) ** 2

    model.zero_grad()
    loss().backward()
    h = 1e-6
    for p in model.parameters():
        old = p.data
        p.data = old + h; up = loss().data
        p.data = old - h; down = loss().data
        p.data = old
        assert abs(p.grad - (up - down) / (2 * h)) < 1e-6


def test_moons_dataset_shape():
    xs, ys = make_moons(n=20)
    assert len(xs) == 20 and set(ys) == {-1.0, 1.0}
