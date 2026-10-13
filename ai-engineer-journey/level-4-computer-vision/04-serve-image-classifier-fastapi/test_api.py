"""Builds an UNTRAINED model checkpoint so the API can be tested without training anything."""
import io
import os

import torch
from PIL import Image

from common import build_model

os.environ["MODEL_PATH"] = "test_model.pt"
torch.save({"state_dict": build_model(3, pretrained=False).state_dict(), "classes": ["cat", "dog", "fish"]}, "test_model.pt")

from fastapi.testclient import TestClient  # noqa: E402
from api import app  # noqa: E402


def png_bytes():
    buf = io.BytesIO()
    Image.new("RGB", (300, 200), (200, 120, 50)).save(buf, format="PNG")
    return buf.getvalue()


def test_predict_returns_a_known_label():
    with TestClient(app) as client:   # "with" runs the lifespan startup (model loading)
        r = client.post("/predict", files={"file": ("x.png", png_bytes(), "image/png")})
        assert r.status_code == 200
        assert r.json()["label"] in ["cat", "dog", "fish"]
        assert abs(sum(t["probability"] for t in r.json()["top"]) - 1) < 1e-3


def test_rejects_non_images():
    with TestClient(app) as client:
        assert client.post("/predict", files={"file": ("x.txt", b"hello", "text/plain")}).status_code == 400
