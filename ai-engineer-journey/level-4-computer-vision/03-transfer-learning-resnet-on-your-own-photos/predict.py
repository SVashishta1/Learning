"""Classify one photo:  python predict.py path/to/photo.jpg"""
import sys

import torch
from PIL import Image

from common import eval_transform, load_checkpoint

model, classes = load_checkpoint("transfer_model.pt")
img = Image.open(sys.argv[1]).convert("RGB")
with torch.no_grad():
    probs = torch.softmax(model(eval_transform(img).unsqueeze(0)), dim=1)[0]
for i in probs.argsort(descending=True)[:3]:
    print(f"{classes[i]:15s} {probs[i]:.1%}")
