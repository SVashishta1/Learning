import os
import tempfile

os.environ["DATABASE_URL"] = f"sqlite:///{tempfile.mkdtemp()}/test.db"
from fastapi.testclient import TestClient  # noqa: E402

import main  # noqa: E402
from fake_llm import FakeClient, text_reply  # noqa: E402

api = TestClient(main.app)


def test_memory_is_sent_back_every_turn():
    fake = FakeClient([text_reply("Nice to meet you, Sam!"), text_reply("Your name is Sam.")])
    main.client = fake
    cid = api.post("/chats", json={}).json()["id"]
    api.post(f"/chats/{cid}/messages", json={"content": "Hi, I'm Sam"})
    r = api.post(f"/chats/{cid}/messages", json={"content": "What's my name?"})
    assert r.json()["reply"] == "Your name is Sam."
    sent = fake.calls[1]["messages"]                      # what the 2nd API call contained
    assert [m["role"] for m in sent] == ["user", "assistant", "user"]
    assert sent[0]["content"] == "Hi, I'm Sam"
    assert len(api.get(f"/chats/{cid}").json()["messages"]) == 4


def test_streaming_saves_the_full_reply():
    main.client = FakeClient([text_reply("Streaming works great")])
    cid = api.post("/chats", json={}).json()["id"]
    body = api.post(f"/chats/{cid}/stream", json={"content": "test"}).text
    assert "Streaming" in body and "[DONE]" in body
    assert api.get(f"/chats/{cid}").json()["messages"][-1]["content"].strip() == "Streaming works great"


def test_unknown_chat_404():
    assert api.post("/chats/9999/messages", json={"content": "hi"}).status_code == 404
