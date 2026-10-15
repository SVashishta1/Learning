"""Builds an UNTRAINED model checkpoint so the API can be tested without training anything."""
import io
import os
import tempfile
from pathlib import Path

import torch
from PIL import Image

from common import build_model

# Save a random-weights model in a temporary folder (deleted automatically) and point the API at it
_tmp = tempfile.TemporaryDirectory()
os.environ["MODEL_PATH"] = str(Path(_tmp.name) / "test_model.pt")
torch.save({"state_dict": build_model(3, pretrained=False).state_dict(), "classes": ["cat", "dog", "fish"]},
           os.environ["MODEL_PATH"])

from fastapi.testclient import TestClient  # noqa: E402
from api import app  # noqa: E402  (imported AFTER setting MODEL_PATH, because api.py reads it on import)


def png_bytes():
    buf = io.BytesIO()
    Image.new("RGB", (300, 200), (200, 120, 50)).save(buf, format="PNG")
    return buf.getvalue()


def test_health_reports_model_loaded():
    with TestClient(app) as client:   # "with" runs the lifespan startup (model loading)
        assert client.get("/health").json() == {"status": "ok", "model_loaded": True, "classes": ["cat", "dog", "fish"]}


def test_predict_returns_a_known_label():
    with TestClient(app) as client:
        r = client.post("/predict", files={"file": ("x.png", png_bytes(), "image/png")})
        assert r.status_code == 200
        assert r.json()["label"] in ["cat", "dog", "fish"]
        assert abs(sum(t["probability"] for t in r.json()["top"]) - 1) < 1e-3


def test_rejects_non_images():
    with TestClient(app) as client:
        assert client.post("/predict", files={"file": ("x.txt", b"hello", "text/plain")}).status_code == 400


def test_rejects_huge_files():
    with TestClient(app) as client:
        big = b"0" * (5 * 1024 * 1024 + 1)
        assert client.post("/predict", files={"file": ("big.png", big, "image/png")}).status_code == 413
