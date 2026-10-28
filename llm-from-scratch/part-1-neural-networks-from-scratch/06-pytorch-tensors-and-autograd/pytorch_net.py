"""Lesson 06, part 3: lesson 05's digit reader rebuilt the "proper" PyTorch way.

nn.Module for the model, torch.optim.SGD for the updates, DataLoader for the batches,
F.cross_entropy for the loss, and autograd for every gradient. Same network, same settings.

Usage:  python pytorch_net.py                 (10 epochs on the CPU, about a minute)
        python pytorch_net.py --device cuda   (if you have an NVIDIA GPU, e.g. on Colab)
"""
import argparse
import time

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import DataLoader, TensorDataset

from mnist import load_mnist


class DigitNet(nn.Module):
    def __init__(self, n_hidden=128):
        super().__init__()
        self.hidden = nn.Linear(784, n_hidden)     # holds W1 (as .weight) and b1 (as .bias)
        self.out = nn.Linear(n_hidden, 10)         # holds W2 and b2
        # Same starting point as lesson 05: He init for the hidden layer, tiny output weights, zero biases.
        nn.init.kaiming_normal_(self.hidden.weight, nonlinearity="relu")
        nn.init.zeros_(self.hidden.bias)
        nn.init.normal_(self.out.weight, std=0.01)
        nn.init.zeros_(self.out.bias)

    def forward(self, x):                          # nn.Module calls this when you write model(x)
        return self.out(F.relu(self.hidden(x)))    # returns logits (raw scores); the loss applies softmax


@torch.no_grad()                                   # evaluation: no gradients needed, so it's faster
def accuracy(model, X, y, device):
    model.eval()
    preds = model(X.to(device)).argmax(dim=1)
    model.train()
    return (preds == y.to(device)).float().mean().item()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--epochs", type=int, default=10)
    parser.add_argument("--lr", type=float, default=0.1)
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument("--device", default="cpu", help="cpu, cuda (NVIDIA) or mps (Apple)")
    args = parser.parse_args()
    torch.manual_seed(0)

    X_train, y_train, X_test, y_test = (torch.from_numpy(a) for a in load_mnist())
    X_val, y_val = X_train[55000:], y_train[55000:]
    X_train, y_train = X_train[:55000], y_train[:55000]
    # TensorDataset pairs images with labels; DataLoader serves shuffled mini-batches of them.
    loader = DataLoader(TensorDataset(X_train, y_train), batch_size=args.batch_size, shuffle=True)

    model = DigitNet().to(args.device)
    optimizer = torch.optim.SGD(model.parameters(), lr=args.lr)
    print(model)
    print(f"{sum(p.numel() for p in model.parameters()):,} parameters on {args.device}")

    start = time.time()
    for epoch in range(1, args.epochs + 1):
        total, batches = 0.0, 0
        for xb, yb in loader:
            xb, yb = xb.to(args.device), yb.to(args.device)
            loss = F.cross_entropy(model(xb), yb)   # 1. forward + loss
            optimizer.zero_grad()                   # 2. clear old grads (they add up!)
            loss.backward()                         # 3. autograd fills p.grad for every parameter
            optimizer.step()                        # 4. p -= lr * p.grad, for every parameter
            total += loss.item()
            batches += 1
        print(f"epoch {epoch}  train loss {total / batches:.4f}  validation accuracy "
              f"{accuracy(model, X_val, y_val, args.device):.2%}  ({time.time() - start:.0f}s)")

    print(f"\nTEST accuracy: {accuracy(model, X_test, y_test, args.device):.2%}")

    torch.save(model.state_dict(), "digit_net.pt")  # state_dict = a dictionary of all the weight tensors
    fresh = DigitNet()
    fresh.load_state_dict(torch.load("digit_net.pt", map_location="cpu"))
    print(f"saved to digit_net.pt and loaded into a fresh model: test accuracy "
          f"{accuracy(fresh, X_test, y_test, 'cpu'):.2%}")


if __name__ == "__main__":
    main()
