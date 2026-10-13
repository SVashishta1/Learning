"""Tests call the API without starting a server. Run: pytest -v"""
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_add():
    r = client.get("/add", params={"a": 2, "b": 3})
    assert r.status_code == 200
    assert r.json()["result"] == 5


def test_divide_by_zero_is_a_400():
    r = client.get("/divide?a=1&b=0")
    assert r.status_code == 400
    assert r.json()["detail"] == "Cannot divide by zero"


def test_missing_parameter_is_a_422():
    # FastAPI validates inputs for free: 422 means "your input has the wrong shape"
    assert client.get("/add?a=2").status_code == 422
