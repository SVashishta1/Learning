"""Run with:  pytest -q   (checks the neuron's maths)."""
import random

from neuron import AND, OR, loss_and_grads, neuron, numeric_grads, sigmoid, train


def test_sigmoid_basics():
    assert sigmoid(0) == 0.5                      # halfway
    assert sigmoid(10) > 0.9999 and sigmoid(-10) < 0.0001


def test_forward_by_hand():
    z, p = neuron([2.0, 3.0], [0.5, -1.0], 1.0)
    assert z == -1.0 and abs(p - 0.2689414) < 1e-6


def test_gradient_check_random_points():
    # The chain-rule gradients must match the "nudge and measure" gradients everywhere.
    random.seed(1)
    for _ in range(5):
        w = [random.uniform(-2, 2), random.uniform(-2, 2)]
        b = random.uniform(-1, 1)
        _, dw, db = loss_and_grads(OR, w, b)
        ndw, ndb = numeric_grads(OR, w, b)
        for a, n in zip(dw + [db], ndw + [ndb]):
            assert abs(a - n) < 1e-5


def test_learns_and():
    w, b = train(AND, report_every=10**9)        # huge report_every = stay quiet
    assert all((neuron(x, w, b)[1] > 0.5) == (y == 1) for x, y in AND)
