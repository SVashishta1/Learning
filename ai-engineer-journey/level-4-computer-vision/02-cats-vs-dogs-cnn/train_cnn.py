"""Project 4.2: cats vs dogs with a Convolutional Neural Network (CNN).

Uses the cat and dog images from CIFAR-10 (10,000 training photos, 32x32 pixels, downloaded automatically ~170 MB).
python train_cnn.py            # train ~10 epochs, saves cat_dog_cnn.pt
python train_cnn.py --smoke    # 10-second check with fake data
"""
import sys

import torch
from torch import nn
from torch.utils.data import DataLoader, Subset, TensorDataset

SMOKE = "--smoke" in sys.argv
EPOCHS = 1 if SMOKE else 10
CAT, DOG = 3, 5                      # CIFAR-10 class numbers
torch.manual_seed(0)
device = "cuda" if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else "cpu"


class CatDogCNN(nn.Module):
    def __init__(self):
        super().__init__()
        # A conv layer slides small 3x3 "pattern detectors" over the image.
        # Early layers find edges, later layers combine them into ears, eyes, fur...
        block = lambda c_in, c_out: nn.Sequential(
            nn.Conv2d(c_in, c_out, 3, padding=1), nn.BatchNorm2d(c_out), nn.ReLU(),
            nn.Conv2d(c_out, c_out, 3, padding=1), nn.BatchNorm2d(c_out), nn.ReLU(),
            nn.MaxPool2d(2))         # halve width/height: keep the strongest signals, shrink the image
        self.features = nn.Sequential(block(3, 32), block(32, 64), block(64, 128))   # 32x32 -> 16 -> 8 -> 4
        self.classifier = nn.Sequential(nn.Flatten(), nn.Dropout(0.3), nn.Linear(128 * 4 * 4, 2))

    def forward(self, x):
        return self.classifier(self.features(x))


def cats_and_dogs(train: bool):
    from torchvision import datasets, transforms
    norm = transforms.Normalize((0.49, 0.48, 0.45), (0.25, 0.24, 0.26))
    tf = transforms.Compose(
        ([transforms.RandomHorizontalFlip(), transforms.RandomCrop(32, padding=4)] if train else [])   # augmentation
        + [transforms.ToTensor(), norm])
    ds = datasets.CIFAR10("data", train=train, download=True, transform=tf)
    keep = [i for i, label in enumerate(ds.targets) if label in (CAT, DOG)]
    ds.targets = [int(t == DOG) for t in ds.targets]          # relabel: 0 = cat, 1 = dog
    return Subset(ds, keep)


if __name__ == "__main__":
    if SMOKE:
        fake = lambda n: TensorDataset(torch.randn(n, 3, 32, 32), torch.randint(0, 2, (n,)))
        train_set, test_set = fake(256), fake(64)
    else:
        train_set, test_set = cats_and_dogs(True), cats_and_dogs(False)
    train_loader = DataLoader(train_set, batch_size=64, shuffle=True)
    test_loader = DataLoader(test_set, batch_size=256)

    model = CatDogCNN().to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=2e-3, weight_decay=1e-4)
    scheduler = torch.optim.lr_scheduler.OneCycleLR(optimizer, max_lr=2e-3, total_steps=EPOCHS * len(train_loader))
    loss_fn = nn.CrossEntropyLoss()
    print(f"{len(train_set)} training images | device {device} | {sum(p.numel() for p in model.parameters()):,} parameters")

    for epoch in range(EPOCHS):
        model.train()
        total_loss = 0.0
        for x, y in train_loader:
            x, y = x.to(device), y.to(device)
            loss = loss_fn(model(x), y)
            optimizer.zero_grad(); loss.backward(); optimizer.step(); scheduler.step()
            total_loss += loss.item()
        model.eval()
        with torch.no_grad():
            correct = sum((model(x.to(device)).argmax(1) == y.to(device)).sum().item() for x, y in test_loader)
        print(f"epoch {epoch + 1:2d} | train loss {total_loss / len(train_loader):.3f} | test accuracy {correct / len(test_set):.1%}")

    torch.save(model.state_dict(), "cat_dog_cnn.pt")
    print("saved cat_dog_cnn.pt")
