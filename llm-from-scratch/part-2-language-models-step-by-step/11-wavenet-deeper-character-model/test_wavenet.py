"""Run with:  pytest -q   (no download needed)."""
import torch

from wavenet import BatchNorm1d, FlattenConsecutive, wavenet


def test_flatten_consecutive_glues_neighbours():
    x = torch.arange(2 * 4 * 3).view(2, 4, 3).float()      # batch 2, 4 positions, 3 channels
    y = FlattenConsecutive(2)(x)
    assert y.shape == (2, 2, 6)
    assert y[0, 0].tolist() == x[0, 0].tolist() + x[0, 1].tolist()   # positions 0 and 1 side by side


def test_batchnorm_uses_batch_and_time_dims():
    torch.manual_seed(0)
    bn = BatchNorm1d(5)
    x = torch.randn(32, 4, 5) * 3 + 7                      # (B, T, C)
    out = bn(x)
    assert torch.allclose(out.mean((0, 1)), torch.zeros(5), atol=1e-5)
    assert bn.running_mean.shape == (5,)                   # one number per channel, not (1, 4, 5)


def test_wavenet_shapes_and_parameter_count():
    torch.manual_seed(42)
    model = wavenet(27)
    assert model(torch.zeros(4, 8, dtype=torch.long)).shape == (4, 27)
    assert sum(p.nelement() for p in model.parameters()) == 76579   # same as the video
