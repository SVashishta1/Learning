"""Project 6.3 part A: LoRA from scratch in plain PyTorch.

LoRA idea: instead of changing a big weight matrix W (d x d), freeze it and learn a SMALL update B @ A
(d x r times r x d, with r tiny, e.g. 4). New output = W x + (B A) x * scale.
"""
import torch
from torch import nn

torch.manual_seed(0)


class LoRALinear(nn.Module):
    def __init__(self, base: nn.Linear, r=4, alpha=8):
        super().__init__()
        self.base = base
        for p in self.base.parameters():
            p.requires_grad = False                                       # the pretrained weights stay frozen
        self.A = nn.Parameter(torch.randn(r, base.in_features) * 0.01)
        self.B = nn.Parameter(torch.zeros(base.out_features, r))          # starts at 0 -> no change at first
        self.scale = alpha / r

    def forward(self, x):
        return self.base(x) + (x @ self.A.T @ self.B.T) * self.scale


# 1. "Pretrain" a model on task A: y = sum of the inputs
d = 64
model = nn.Sequential(nn.Linear(d, d), nn.ReLU(), nn.Linear(d, 1))
X = torch.randn(2000, d)
task_a, task_b = X.sum(1, keepdim=True), (X[:, :d // 2].sum(1) - X[:, d // 2:].sum(1)).unsqueeze(1)


def fit(model, y, steps=600):
    opt = torch.optim.Adam([p for p in model.parameters() if p.requires_grad], lr=1e-2)
    for _ in range(steps):
        loss = nn.functional.mse_loss(model(X), y)
        opt.zero_grad(); loss.backward(); opt.step()
    return loss.item()


print(f"pretrained on task A, loss {fit(model, task_a):.3f}")
print(f"same model on NEW task B before adapting: loss {nn.functional.mse_loss(model(X), task_b).item():.1f}")

# 2. Wrap both Linear layers with LoRA and train ONLY the small A/B matrices on task B
model[0], model[2] = LoRALinear(model[0], r=4), LoRALinear(model[2], r=4)
trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
total = sum(p.numel() for p in model.parameters())
print(f"LoRA trains {trainable:,} of {total:,} parameters ({trainable / total:.1%})")
print(f"after LoRA fine-tuning on task B: loss {fit(model, task_b):.3f}")
