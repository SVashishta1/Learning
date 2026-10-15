from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_random_joke_in_category():
    assert client.get("/jokes/random?category=ai").json()["category"] == "ai"


def test_unknown_joke_is_404():
    assert client.get("/jokes/999").status_code == 404


def test_add_joke_then_read_it():
    r = client.post("/jokes", json={"text": "A brand new joke!", "category": "ai"})
    assert r.status_code == 201
    assert client.get(f"/jokes/{r.json()['id']}").json()["text"] == "A brand new joke!"


def test_too_short_joke_rejected():
    assert client.post("/jokes", json={"text": "hi"}).status_code == 422


def test_unknown_category_is_404():
    assert client.get("/jokes/random?category=cooking").status_code == 404


def test_random_quote():
    assert "quote" in client.get("/quotes/random").json()
