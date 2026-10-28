"""Run with:  pytest -q
Gradient checks: for many small formulas, the engine's grads must equal the
"nudge each input and measure" slopes, and (if installed) PyTorch's grads."""
import math
import random

import pytest

from engine import Value

# Each formula takes two Values (or plain floats) and uses a different mix of operations.
FORMULAS = {
    "add_mul": lambda a, b: a * b + a,
    "pow_div": lambda a, b: (a**2) / (b + 5.0),
    "tanh": lambda a, b: (a * 0.5 + b).tanh(),
    "exp_log": lambda a, b: (a.exp() + b * b).log() if isinstance(a, Value) else math.log(math.exp(a) + b * b),
    "relu_sub": lambda a, b: (a - b).relu() * 3.0 - 2.0 / (b * b + 1.0),
    "reused": lambda a, b: (a * b) * (a + b) + a,
}


def numeric_slope(fn, a, b, which, h=1e-6):
    """Plain-float version of the formula, nudged on one input (central difference)."""
    plain = lambda x, y: fn(Value(x), Value(y)).data
    if which == 0:
        return (plain(a + h, b) - plain(a - h, b)) / (2 * h)
    return (plain(a, b + h) - plain(a, b - h)) / (2 * h)


@pytest.mark.parametrize("name", FORMULAS)
def test_gradients_match_nudging(name):
    fn = FORMULAS[name]
    random.seed(0)
    for _ in range(10):
        a_val, b_val = random.uniform(-2, 2), random.uniform(-2, 2)
        a, b = Value(a_val), Value(b_val)
        out = fn(a, b)
        out.backward()
        assert math.isclose(a.grad, numeric_slope(fn, a_val, b_val, 0), abs_tol=1e-4)
        assert math.isclose(b.grad, numeric_slope(fn, a_val, b_val, 1), abs_tol=1e-4)


def test_hand_example():
    a, b, c, f = Value(2.0), Value(-3.0), Value(10.0), Value(-2.0)
    L = (a * b + c) * f
    L.backward()
    assert (L.data, a.grad, b.grad, c.grad, f.grad) == (-8.0, 6.0, -4.0, -2.0, 4.0)


def test_grad_accumulates_when_value_is_reused():
    a = Value(3.0)
    (a + a).backward()
    assert a.grad == 2.0


def test_matches_pytorch():
    torch = pytest.importorskip("torch")
    x = Value(-4.0)
    z = 2 * x + 2 + x
    q = z.relu() + z * x
    h = (z * z).relu()
    y = h + q + q * x
    y.backward()
    xt = torch.tensor([-4.0], dtype=torch.double, requires_grad=True)
    zt = 2 * xt + 2 + xt
    qt = zt.relu() + zt * xt
    ht = (zt * zt).relu()
    yt = ht + qt + qt * xt
    yt.backward()
    assert math.isclose(y.data, yt.item()) and math.isclose(x.grad, xt.grad.item())
