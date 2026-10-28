"""Run with:  pytest -q   (no download needed: random stand-in data)."""
import numpy as np
import torch

from compare_grads import compare
from pytorch_net import DigitNet


def test_numpy_and_torch_gradients_agree():
    rng = np.random.default_rng(3)
    X = rng.random((16, 784))                      # 16 random "images"
    y = rng.integers(0, 10, 16)
    assert compare(X, y, verbose=False) < 1e-10


def test_digitnet_shapes_and_first_loss():
    torch.manual_seed(0)
    model = DigitNet()
    logits = model(torch.rand(8, 784))
    assert logits.shape == (8, 10)
    loss = torch.nn.functional.cross_entropy(logits, torch.arange(8))
    assert abs(loss.item() - np.log(10)) < 0.05     # small output weights -> fair 10-way guess


def test_autograd_square():
    x = torch.tensor([1.0, 2.0, 3.0], requires_grad=True)
    (x**2).sum().backward()
    assert x.grad.tolist() == [2.0, 4.0, 6.0]
