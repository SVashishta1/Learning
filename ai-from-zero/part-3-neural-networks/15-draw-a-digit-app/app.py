# A web page where you draw a digit and the model from project 14 reads it live.
# Run: copy ../14-read-handwritten-digits/digit_brain.pt here, then: uvicorn app:app --reload
import base64
import io

import numpy as np
import torch
from fastapi import FastAPI
from fastapi.responses import FileResponse
from PIL import Image
from pydantic import BaseModel

brain = torch.nn.Sequential(torch.nn.Flatten(), torch.nn.Linear(784, 128), torch.nn.ReLU(), torch.nn.Linear(128, 10))
brain.load_state_dict(torch.load("digit_brain.pt"))      # the brain you trained in project 14
app = FastAPI()


class Drawing(BaseModel):
    image: str        # the drawing, sent by the web page as text ("base64")


def make_it_look_like_mnist(img):
    """MNIST digits are white on black, about 20x20 pixels, centred in a 28x28 box. Make the drawing match."""
    pixels = np.array(img.convert("L"))
    rows, cols = np.nonzero(pixels > 30)
    if len(rows) == 0:
        return None
    digit = Image.fromarray(pixels[rows.min():rows.max() + 1, cols.min():cols.max() + 1])
    digit.thumbnail((20, 20))
    box = Image.new("L", (28, 28))
    box.paste(digit, ((28 - digit.width) // 2, (28 - digit.height) // 2))
    return torch.tensor(np.array(box), dtype=torch.float32).view(1, 1, 28, 28) / 255


@app.post("/predict")
def predict(drawing: Drawing):
    img = Image.open(io.BytesIO(base64.b64decode(drawing.image.split(",")[1])))
    x = make_it_look_like_mnist(img)
    if x is None:
        return {"digit": None, "confidence": [0] * 10}
    with torch.no_grad():
        confidence = torch.softmax(brain(x), dim=1)[0]
    return {"digit": int(confidence.argmax()), "confidence": [round(c, 3) for c in confidence.tolist()]}


@app.get("/")
def page():
    return FileResponse("page.html")
