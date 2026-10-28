"""Lesson 21: the offline assistant (FAKE and a stub local model server) and the egress check."""
import json

import httpx
import pytest
from fastapi.testclient import TestClient

import assistant
import verify_no_egress


@pytest.fixture(autouse=True)
def fresh(monkeypatch, tmp_path):
    monkeypatch.setattr(assistant, "AUDIT_LOG", tmp_path / "audit.jsonl")
    monkeypatch.setattr(assistant, "_index", None)


def test_search_finds_the_right_procedure_offline():
    hits = assistant.Index().search("the temperature logger shows an alarm when the pallet arrives")
    assert hits[0]["id"] == "cold-chain#logger-alarm-on-arrival"


def test_ask_answers_with_sources_and_writes_the_audit_log():
    c = TestClient(assistant.app)
    r = c.post("/ask", json={"question": "A package is leaking, what do I do?", "user": "sam"}).json()
    assert r["sources"][0]["id"] == "dangerous-goods#leaking-package" and "2222" in r["answer"]
    entry = json.loads(assistant.AUDIT_LOG.read_text().splitlines()[0])
    assert entry["user"] == "sam" and entry["sources"][0] == "dangerous-goods#leaking-package"
    assert c.get("/ready").json() == {"ready": True, "mode": "fake"}
    assert "Warehouse assistant" in c.get("/").text


def test_real_mode_talks_openai_compatible_api_to_the_local_server(monkeypatch):
    calls = []

    def server(request):                        # pretends to be Ollama / vLLM
        calls.append(request.url.path)
        if request.url.path.endswith("/embeddings"):
            texts = json.loads(request.content)["input"]
            return httpx.Response(200, json={"data": [{"index": i, "embedding": assistant.fake_embed(t)} for i, t in enumerate(texts)]})
        if request.url.path.endswith("/models"):
            return httpx.Response(200, json={"data": [{"id": "qwen2.5:7b"}, {"id": "nomic-embed-text:latest"}]})
        body = json.loads(request.content)
        assert "[cold-chain#reefer-trailer-failure]" in body["messages"][1]["content"]
        return httpx.Response(200, json={"choices": [{"message": {"content": "Plug it into dock 14 [cold-chain#reefer-trailer-failure]"}}]})
    monkeypatch.setattr(assistant, "FAKE", False)
    monkeypatch.setattr(assistant, "http", httpx.Client(transport=httpx.MockTransport(server), base_url="http://ollama:11434"))
    monkeypatch.setattr(assistant, "MODEL_URL", "http://ollama:11434/v1")
    c = TestClient(assistant.app)
    assert c.get("/ready").json()["mode"] == "local-model"
    r = c.post("/ask", json={"question": "The reefer trailer cooling unit failed in the yard"}).json()
    assert r["answer"].startswith("Plug it into dock 14") and calls.count("/v1/chat/completions") == 1


def test_ready_fails_when_model_missing(monkeypatch):
    monkeypatch.setattr(assistant, "FAKE", False)
    monkeypatch.setattr(assistant, "http", httpx.Client(transport=httpx.MockTransport(
        lambda r: httpx.Response(200, json={"data": [{"id": "llama3.2:3b"}]}))))
    r = TestClient(assistant.app).get("/ready")
    assert r.status_code == 503 and "qwen2.5:7b" in r.json()["detail"]


def test_verify_no_egress(monkeypatch, capsys):
    monkeypatch.setenv("FAKE_LLM", "1")
    monkeypatch.setattr(verify_no_egress, "reachable", lambda h, p: "blocked (OSError)")
    assert verify_no_egress.main() == 0
    monkeypatch.setattr(verify_no_egress, "reachable", lambda h, p: "REACHABLE" if h == "pypi.org" else "no DNS")
    assert verify_no_egress.main() == 1
    assert "NOT ISOLATED" in capsys.readouterr().out
