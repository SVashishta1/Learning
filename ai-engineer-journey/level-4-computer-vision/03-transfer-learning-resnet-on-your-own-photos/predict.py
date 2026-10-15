"""Classify one photo:  python predict.py path/to/photo.jpg"""
import sys

import torch
from PIL import Image

from common import eval_transform, load_checkpoint

if len(sys.argv) != 2:
    sys.exit("Usage: python predict.py path/to/photo.jpg")

model, classes = load_checkpoint("transfer_model.pt")      # trained by train_transfer.py
img = Image.open(sys.argv[1]).convert("RGB")                # convert: PNGs with transparency, greyscale photos...
with torch.no_grad():                                       # just predicting, no learning: skip gradients
    probs = torch.softmax(model(eval_transform(img).unsqueeze(0)), dim=1)[0]
for i in probs.argsort(descending=True)[:3]:            # the 3 most likely classes, best first
    print(f"{classes[i]:15s} {probs[i]:.1%}")
