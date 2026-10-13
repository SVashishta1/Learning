"""No photos of your own yet? This builds a demo dataset (airplane / car / ship) from CIFAR-10
in the exact folder layout you'd use for your own photos."""
from pathlib import Path

from torchvision import datasets

PICK = {0: "airplane", 1: "car", 8: "ship"}
for split, train in [("train", True), ("val", False)]:
    ds = datasets.CIFAR10("data/cifar", train=train, download=True)
    counts = {c: 0 for c in PICK}
    limit = 150 if train else 50
    for img, label in ds:
        if label in PICK and counts[label] < limit:
            folder = Path("dataset") / split / PICK[label]
            folder.mkdir(parents=True, exist_ok=True)
            img.resize((224, 224)).save(folder / f"{counts[label]}.jpg")
            counts[label] += 1
        if all(v >= limit for v in counts.values()):
            break
print("Done: dataset/train/{airplane,car,ship} and dataset/val/...")
