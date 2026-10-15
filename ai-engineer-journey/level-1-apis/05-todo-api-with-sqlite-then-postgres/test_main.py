import os
import tempfile

# Use a throwaway SQLite file for tests so we never touch your real data.
# To run the same tests against PostgreSQL instead, set TEST_DATABASE_URL first (see README).
os.environ["DATABASE_URL"] = os.getenv("TEST_DATABASE_URL", f"sqlite:///{tempfile.mkdtemp()}/test.db")

from fastapi.testclient import TestClient  # noqa: E402
from main import app  # noqa: E402

client = TestClient(app)


def test_create_and_persist():
    tid = client.post("/todos", json={"title": "persist me"}).json()["id"]
    assert client.get(f"/todos/{tid}").json()["title"] == "persist me"
    client.patch(f"/todos/{tid}", json={"done": True})
    assert tid in [t["id"] for t in client.get("/todos?done=true").json()]
    assert tid not in [t["id"] for t in client.get("/todos?done=false").json()]
    assert client.delete(f"/todos/{tid}").status_code == 204
    assert client.get(f"/todos/{tid}").status_code == 404


def test_patch_null_title_is_ignored():
    tid = client.post("/todos", json={"title": "keep me"}).json()["id"]
    r = client.patch(f"/todos/{tid}", json={"title": None})
    assert r.status_code == 200 and r.json()["title"] == "keep me"


def test_empty_title_rejected():
    assert client.post("/todos", json={"title": ""}).status_code == 422
