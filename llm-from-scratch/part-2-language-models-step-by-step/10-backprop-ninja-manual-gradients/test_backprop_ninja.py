"""Run with:  pytest -q   (random stand-in data, no download)."""
import torch

from backprop_ninja import fast_dhprebn, fast_dlogits, run_all


def test_every_hand_written_gradient_matches_pytorch():
    g = torch.Generator().manual_seed(0)
    Xb = torch.randint(0, 27, (32, 3), generator=g)
    Yb = torch.randint(0, 27, (32,), generator=g)
    assert run_all(Xb, Yb, verbose=False)


def test_fast_dlogits_rows_sum_to_zero():
    # probs add to 1 and we subtract exactly 1 per row, so each row of dlogits adds to 0
    logits = torch.randn(8, 27)
    d = fast_dlogits(logits, torch.arange(8))
    assert torch.allclose(d.sum(1), torch.zeros(8), atol=1e-7)


def test_fast_batchnorm_backward_numerically():
    torch.manual_seed(0)
    x = torch.randn(16, 5, dtype=torch.double, requires_grad=True)
    gain = torch.rand(1, 5, dtype=torch.double) + 0.5
    var_inv = (x.var(0, keepdim=True) + 1e-5) ** -0.5
    raw = (x - x.mean(0, keepdim=True)) * var_inv
    out = gain * raw
    upstream = torch.randn(16, 5, dtype=torch.double)
    (out * upstream).sum().backward()
    ours = fast_dhprebn(gain, var_inv.detach(), raw.detach(), upstream)
    assert torch.allclose(ours, x.grad)
