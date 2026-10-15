import os
import tempfile

os.environ["DATABASE_URL"] = f"sqlite:///{tempfile.mkdtemp()}/test.db"
from fastapi.testclient import TestClient  # noqa: E402
from main import app, fix_db_url  # noqa: E402

client = TestClient(app)


def login(username, password):
    return client.post("/login", data={"username": username, "password": password})


def test_signup_login_and_private_todos():
    assert client.post("/signup", json={"username": "ana", "password": "supersecret1"}).status_code == 201
    assert client.post("/signup", json={"username": "ben", "password": "supersecret2"}).status_code == 201
    ana = {"Authorization": f"Bearer {login('ana', 'supersecret1').json()['access_token']}"}
    ben = {"Authorization": f"Bearer {login('ben', 'supersecret2').json()['access_token']}"}

    client.post("/todos", json={"title": "ana's secret plan"}, headers=ana)
    assert [t["title"] for t in client.get("/todos", headers=ana).json()] == ["ana's secret plan"]
    assert client.get("/todos", headers=ben).json() == []          # ben can't see ana's todos


def test_wrong_password_and_missing_token():
    client.post("/signup", json={"username": "cat", "password": "rightpassword"})
    assert login("cat", "wrongpassword").status_code == 401
    assert client.get("/me").status_code == 401
    assert client.get("/me", headers={"Authorization": "Bearer not-a-real-token"}).status_code == 401


def test_duplicate_username():
    client.post("/signup", json={"username": "dup", "password": "password123"})
    assert client.post("/signup", json={"username": "dup", "password": "password123"}).status_code == 409


def test_password_rules():
    # 40 x "é" is only 40 characters but 80 bytes: too long for bcrypt, so a clean 422 (not a crash)
    assert client.post("/signup", json={"username": "emo", "password": "é" * 40}).status_code == 422
    assert client.post("/signup", json={"username": "short", "password": "abc"}).status_code == 422
    assert login("short", "x" * 100).status_code == 401      # absurdly long login attempt: 401, not 500


def test_todos_need_a_token():
    assert client.post("/todos", json={"title": "sneaky"}).status_code == 401


def test_fix_db_url():
    assert fix_db_url("postgresql://u:p@host/db") == "postgresql+psycopg://u:p@host/db"
    assert fix_db_url("postgres://u:p@host/db") == "postgresql+psycopg://u:p@host/db"
    assert fix_db_url("sqlite:///./app.db") == "sqlite:///./app.db"
