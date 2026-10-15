"""Project 4.5: draw a digit in the browser, the MNIST model from 4.1 guesses it live."""
import base64
import binascii
import io
import os

import numpy as np
import torch
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from PIL import Image, UnidentifiedImageError
from pydantic import BaseModel

from model import DigitNet

MODEL_PATH = os.getenv("MODEL_PATH", "mnist_mlp.pt")   # the file trained in project 4.1
app = FastAPI(title="Draw a digit")
model = DigitNet()                                      # random weights until we load the trained ones
if os.path.exists(MODEL_PATH):
    model.load_state_dict(torch.load(MODEL_PATH, map_location="cpu"))   # load ONCE at startup
model.eval()


def to_mnist(img: Image.Image) -> torch.Tensor:
    """Make a canvas drawing look like an MNIST digit: white on black, fit into 20x20, centred in 28x28."""
    a = np.array(img.convert("L"), dtype=np.float32)       # "L" = greyscale: one number (0-255) per pixel
    ys, xs = np.nonzero(a > 30)                            # coordinates of the "ink" pixels
    if len(xs) == 0:
        raise HTTPException(400, "The canvas is empty")
    crop = Image.fromarray(a[ys.min():ys.max() + 1, xs.min():xs.max() + 1].astype(np.uint8))  # cut out the digit
    scale = 20 / max(crop.size)                            # longest side becomes 20 pixels, keeping the shape
    crop = crop.resize((max(1, round(crop.width * scale)), max(1, round(crop.height * scale))), Image.LANCZOS)
    canvas = Image.new("L", (28, 28))
    canvas.paste(crop, ((28 - crop.width) // 2, (28 - crop.height) // 2))
    x = torch.tensor(np.array(canvas), dtype=torch.float32) / 255
    return ((x - 0.1307) / 0.3081).view(1, 1, 28, 28)    # same normalisation as training


class Drawing(BaseModel):
    image: str      # "data:image/png;base64,...." straight from canvas.toDataURL()


@app.post("/predict")
def predict(d: Drawing):
    try:
        raw = base64.b64decode(d.image.split(",")[-1])     # drop the "data:image/png;base64," prefix
        img = Image.open(io.BytesIO(raw))
    except (binascii.Error, UnidentifiedImageError, OSError):
        raise HTTPException(400, "image must be a base64-encoded PNG")
    with torch.no_grad():
        probs = torch.softmax(model(to_mnist(img)), dim=1)[0]
    return {"digit": int(probs.argmax()), "probabilities": [round(p, 4) for p in probs.tolist()],
            "trained": os.path.exists(MODEL_PATH)}


@app.get("/")
def home():
    return FileResponse(os.path.join(os.path.dirname(__file__), "static", "index.html"))
