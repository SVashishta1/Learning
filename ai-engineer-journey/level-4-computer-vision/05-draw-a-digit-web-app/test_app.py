import base64
import io

from fastapi.testclient import TestClient
from PIL import Image, ImageDraw

from app import app

client = TestClient(app)


def drawing_of_a_line():
    img = Image.new("RGB", (280, 280), "black")
    ImageDraw.Draw(img).line([(140, 40), (140, 240)], fill="white", width=20)   # looks like a "1"
    buf = io.BytesIO(); img.save(buf, format="PNG")
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


def test_predict_shape():
    r = client.post("/predict", json={"image": drawing_of_a_line()})
    assert r.status_code == 200
    assert 0 <= r.json()["digit"] <= 9 and len(r.json()["probabilities"]) == 10


def test_empty_canvas_is_400():
    buf = io.BytesIO(); Image.new("RGB", (280, 280), "black").save(buf, format="PNG")
    assert client.post("/predict", json={"image": base64.b64encode(buf.getvalue()).decode()}).status_code == 400


def test_homepage():
    assert "Draw a digit" in client.get("/").text
