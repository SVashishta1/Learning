"""Automatic checks for main.py. Run them with:  pytest -v"""

from fastapi.testclient import TestClient

from main import app, predict_mood

# TestClient pretends to be a browser: it calls the API without starting a server.
client = TestClient(app)


def test_health_says_ok():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_happy_sentence_is_positive():
    assert predict_mood("I love this, it is great!")["label"] == "positive"


def test_sad_sentence_is_negative():
    assert predict_mood("This is terrible and I am sad")["label"] == "negative"


def test_plain_sentence_is_neutral():
    assert predict_mood("The meeting is at three")["label"] == "neutral"


def test_predict_endpoint_returns_label_and_score():
    response = client.post("/predict", json={"text": "What an amazing day"})
    assert response.status_code == 200
    assert response.json() == {
        "text": "What an amazing day",
        "label": "positive",
        "score": 1,
    }


def test_empty_text_is_rejected():
    # 422 = "I understood the request, but the input breaks the rules".
    response = client.post("/predict", json={"text": ""})
    assert response.status_code == 422
