"""Run with:  pytest -q   (no download needed: these tests use small random data)."""
import numpy as np

from numpy_net import gradient_check, init_params, loss_and_grads, softmax


def test_softmax_rows_add_to_one_even_for_huge_scores():
    probs = softmax(np.array([[1000.0, 1000.0, 0.0], [1.0, 2.0, 3.0]]))
    assert np.allclose(probs.sum(axis=1), 1.0)
    assert np.allclose(probs[0], [0.5, 0.5, 0.0])        # no overflow thanks to the max trick


def test_hand_written_gradients_match_nudging():
    assert gradient_check(seed=1) < 1e-6
    assert gradient_check(seed=2) < 1e-6


def test_first_loss_is_a_fair_guess():
    params = init_params(seed=0)
    X = np.random.default_rng(0).random((200, 784)).astype(np.float32)
    y = np.arange(200) % 10
    loss, grads = loss_and_grads(params, X, y)
    assert abs(loss - np.log(10)) < 0.05                   # about -ln(1/10) = 2.3026
    assert all(grads[k].shape == params[k].shape for k in params)


def test_a_few_steps_reduce_the_loss():
    rng = np.random.default_rng(0)
    X = rng.random((64, 784)).astype(np.float32)
    y = rng.integers(0, 10, 64)
    params = init_params(seed=0)
    first, _ = loss_and_grads(params, X, y)
    for _ in range(50):
        loss, grads = loss_and_grads(params, X, y)
        for k in params:
            params[k] -= 0.1 * grads[k]
    assert loss < first / 2                                # it can memorise one small batch
