from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_full_crud_lifecycle():
    created = client.post("/todos", json={"title": "learn FastAPI"})
    assert created.status_code == 201
    tid = created.json()["id"]

    assert client.get(f"/todos/{tid}").json()["title"] == "learn FastAPI"

    updated = client.patch(f"/todos/{tid}", json={"done": True})
    assert updated.json()["done"] is True
    assert updated.json()["title"] == "learn FastAPI"      # untouched field kept

    assert tid in [t["id"] for t in client.get("/todos?done=true").json()]

    assert client.delete(f"/todos/{tid}").status_code == 204
    assert client.get(f"/todos/{tid}").status_code == 404


def test_empty_title_rejected():
    assert client.post("/todos", json={"title": ""}).status_code == 422
