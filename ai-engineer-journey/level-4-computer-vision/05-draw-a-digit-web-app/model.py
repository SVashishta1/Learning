"""Same network as project 4.1 (copied so this folder is self-contained)."""
from torch import nn


class DigitNet(nn.Module):
    def __init__(self):
        super().__init__()
        self.net = nn.Sequential(nn.Flatten(), nn.Linear(784, 128), nn.ReLU(), nn.Linear(128, 64), nn.ReLU(), nn.Linear(64, 10))

    def forward(self, x):
        return self.net(x)
