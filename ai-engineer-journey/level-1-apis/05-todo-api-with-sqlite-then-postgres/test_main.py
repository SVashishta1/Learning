import os
import tempfile

# Use a throwaway database file for tests so we never touch your real data
os.environ["DATABASE_URL"] = f"sqlite:///{tempfile.mkdtemp()}/test.db"

from fastapi.testclient import TestClient  # noqa: E402
from main import app  # noqa: E402

client = TestClient(app)


def test_create_and_persist():
    tid = client.post("/todos", json={"title": "persist me"}).json()["id"]
    assert client.get(f"/todos/{tid}").json()["title"] == "persist me"
    client.patch(f"/todos/{tid}", json={"done": True})
    assert [t["id"] for t in client.get("/todos?done=true").json()] == [tid]
    assert client.delete(f"/todos/{tid}").status_code == 204
    assert client.get(f"/todos/{tid}").status_code == 404
