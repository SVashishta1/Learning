"""Project 4.1: recognise handwritten digits (0-9) with a simple fully-connected network.

python train_mnist.py           # downloads MNIST (~12 MB), trains 3 epochs, saves mnist_mlp.pt
python train_mnist.py --smoke   # 10-second check with fake data (no download)
"""
import sys

import torch
from torch import nn
from torch.utils.data import DataLoader, TensorDataset

SMOKE = "--smoke" in sys.argv
torch.manual_seed(0)
device = "cuda" if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else "cpu"


class DigitNet(nn.Module):
    """28x28 image -> flatten to 784 numbers -> 128 -> 64 -> 10 scores (one per digit)."""
    def __init__(self):
        super().__init__()
        self.net = nn.Sequential(
            nn.Flatten(),
            nn.Linear(28 * 28, 128), nn.ReLU(),
            nn.Linear(128, 64), nn.ReLU(),
            nn.Linear(64, 10),            # raw scores ("logits"); CrossEntropyLoss applies softmax for us
        )

    def forward(self, x):
        return self.net(x)


def get_data():
    if SMOKE:
        fake = lambda n: TensorDataset(torch.rand(n, 1, 28, 28), torch.randint(0, 10, (n,)))
        return fake(512), fake(128)
    from torchvision import datasets, transforms
    tf = transforms.Compose([transforms.ToTensor(), transforms.Normalize((0.1307,), (0.3081,))])  # pixels -> ~mean 0, std 1
    return (datasets.MNIST("data", train=True, download=True, transform=tf),
            datasets.MNIST("data", train=False, download=True, transform=tf))


def evaluate(model, loader):
    model.eval()                                   # switch off training-only behaviour (dropout etc.)
    correct = total = 0
    with torch.no_grad():                          # no gradients needed for testing = faster
        for x, y in loader:
            correct += (model(x.to(device)).argmax(1) == y.to(device)).sum().item()
            total += len(y)
    return correct / total


def ascii_digit(img):
    chars = " .:-=+*#%@"
    return "\n".join("".join(chars[min(9, int((v + 0.5) * 6))] for v in row[::2]) for row in img[0][::2])


if __name__ == "__main__":
    train_set, test_set = get_data()
    train_loader = DataLoader(train_set, batch_size=64, shuffle=True)   # shuffle so batches differ every epoch
    test_loader = DataLoader(test_set, batch_size=256)

    model = DigitNet().to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)
    loss_fn = nn.CrossEntropyLoss()
    print(f"device: {device} | parameters: {sum(p.numel() for p in model.parameters()):,}")

    for epoch in range(1 if SMOKE else 3):
        model.train()
        for i, (x, y) in enumerate(train_loader):
            x, y = x.to(device), y.to(device)
            loss = loss_fn(model(x), y)            # 1. forward + loss
            optimizer.zero_grad()                  # 2. clear old gradients
            loss.backward()                        # 3. backprop (micrograd, but for tensors!)
            optimizer.step()                       # 4. update weights
            if i % 300 == 0:
                print(f"epoch {epoch + 1} batch {i:4d} | loss {loss.item():.3f}")
        print(f"epoch {epoch + 1} test accuracy: {evaluate(model, test_loader):.2%}")

    if SMOKE:
        print("smoke run: not saving (a model trained on random noise would overwrite your real one)")
    else:
        torch.save(model.state_dict(), "mnist_mlp.pt")   # only the learned numbers, not the code
        print("saved mnist_mlp.pt")

    x, y = test_set[0]                             # the first test image and its true label
    model.eval()
    with torch.no_grad():
        pred = model(x.unsqueeze(0).to(device)).argmax(1).item()   # unsqueeze(0): a "batch" of 1 image
    print(ascii_digit(x.numpy()))
    print(f"model says: {pred} | truth: {y}")
