"""Project 4.3: teach a pretrained ResNet-18 YOUR classes with only ~30-100 photos per class.

Folder layout (one sub-folder per class):
    dataset/train/apple/*.jpg   dataset/train/banana/*.jpg   ...
    dataset/val/apple/*.jpg     dataset/val/banana/*.jpg     ...

python train_transfer.py            # trains, saves transfer_model.pt
python train_transfer.py --smoke    # fake data, random weights, no downloads
"""
import sys

import torch
from torch import nn
from torch.utils.data import DataLoader, TensorDataset

from common import build_model, eval_transform, train_transform

SMOKE = "--smoke" in sys.argv
device = "cuda" if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else "cpu"

if SMOKE:
    classes = ["apple", "banana", "cherry"]
    fake = lambda n: TensorDataset(torch.randn(n, 3, 224, 224), torch.randint(0, 3, (n,)))
    train_set, val_set = fake(16), fake(8)
else:
    from torchvision.datasets import ImageFolder
    train_set = ImageFolder("dataset/train", transform=train_transform)   # labels = folder names!
    val_set = ImageFolder("dataset/val", transform=eval_transform)
    classes = train_set.classes
print("classes:", classes)

model = build_model(len(classes), pretrained=not SMOKE).to(device)
trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
print(f"trainable parameters: {trainable:,} of {sum(p.numel() for p in model.parameters()):,}")

train_loader = DataLoader(train_set, batch_size=16, shuffle=True)
val_loader = DataLoader(val_set, batch_size=32)
optimizer = torch.optim.Adam([p for p in model.parameters() if p.requires_grad], lr=1e-3)
loss_fn = nn.CrossEntropyLoss()

for epoch in range(1 if SMOKE else 5):
    model.train()
    for x, y in train_loader:
        loss = loss_fn(model(x.to(device)), y.to(device))
        optimizer.zero_grad(); loss.backward(); optimizer.step()
    model.eval()
    with torch.no_grad():
        correct = sum((model(x.to(device)).argmax(1).cpu() == y).sum().item() for x, y in val_loader)
    print(f"epoch {epoch + 1} | last batch loss {loss.item():.3f} | val accuracy {correct / len(val_set):.1%}")

torch.save({"state_dict": model.state_dict(), "classes": classes}, "transfer_model.pt")
print("saved transfer_model.pt (copy it to project 4.4 to serve it)")
