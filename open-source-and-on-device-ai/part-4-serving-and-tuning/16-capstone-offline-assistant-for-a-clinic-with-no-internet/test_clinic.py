"""Tests that run WITHOUT Ollama: a fake Ollama answers inside the test (httpx.MockTransport).

Run:  pytest -q
"""
import json

import httpx
import pytest
from fastapi.testclient import TestClient

import app as webapp
import audit
import clinic_rag

WORDS = ["fever", "ors", "sachet", "wound", "burn", "fridge", "vaccine", "referral", "danger", "bleeding"]


def fake_vector(text):
    """A pretend embedding: how often each keyword appears (enough to test the search logic)."""
    text = text.lower()
    return [text.count(w) + 0.01 for w in WORDS]


def fake_ollama(request):
    body = json.loads(request.content or b"{}")
    if request.url.path == "/api/embed":
        return httpx.Response(200, json={"embeddings": [fake_vector(t) for t in body["input"]]})
    if request.url.path == "/api/chat":
        excerpts = body["messages"][-1]["content"]
        return httpx.Response(200, json={"message": {"role": "assistant",
                                                     "content": f"Answer based on [1]. ({len(excerpts)} chars of excerpts)"}})
    if request.url.path == "/api/tags":
        return httpx.Response(200, json={"models": [{"name": "llama3.2:3b"}, {"name": "nomic-embed-text:latest"}]})
    return httpx.Response(404, json={"error": "not found"})


@pytest.fixture(autouse=True)
def offline_setup(tmp_path, monkeypatch):
    monkeypatch.setattr(clinic_rag, "ollama", httpx.Client(base_url="http://fake", transport=httpx.MockTransport(fake_ollama)))
    monkeypatch.setattr(clinic_rag, "DATA", tmp_path)
    monkeypatch.setattr(clinic_rag, "DB", tmp_path / "clinic.db")
    monkeypatch.setattr(audit, "LOG", tmp_path / "audit.jsonl")
    webapp.index.cache_clear()
    clinic_rag.build_index()


def test_chunks_keep_title_and_section():
    text = (clinic_rag.PROTOCOLS / "02-dehydration-and-ors.md").read_text()
    chunks = clinic_rag.chunk(text)
    assert len(chunks) >= 4
    assert all(c[1].startswith("Diarrhoea and dehydration") for c in chunks)
    assert "FICTIONAL" not in "".join(c[1] for c in chunks)       # the disclaimer is not indexed as content


def test_search_finds_the_right_protocol():
    hits = clinic_rag.search("How many litres of water for one ORS sachet?", clinic_rag.load_index())
    assert hits[0]["file"] == "02-dehydration-and-ors.md"


def test_ask_answers_and_writes_audit_log():
    client = TestClient(webapp.app)
    response = client.post("/api/ask", json={"staff_id": "nurse-1", "question": "How do I store vaccines in the fridge?"})
    assert response.status_code == 200
    data = response.json()
    assert "[1]" in data["answer"] and data["sources"][0]["file"] == "06-vaccine-fridge-cold-chain.md"
    record = json.loads(audit.LOG.read_text().splitlines()[-1])
    assert record["staff_id"] == "nurse-1" and record["hash"].startswith(data["audit_id"])
    assert audit.verify()[0]


def test_bad_staff_id_is_rejected():
    client = TestClient(webapp.app)
    response = client.post("/api/ask", json={"staff_id": "<script>", "question": "fever?"})
    assert response.status_code == 422


def test_tampering_is_detected():
    for i in range(3):
        audit.log({"event": "answer", "staff_id": "s", "question": f"q{i}"})
    lines = audit.LOG.read_text().splitlines()
    lines[1] = lines[1].replace('"q1"', '"edited"')
    audit.LOG.write_text("\n".join(lines) + "\n")
    ok, message = audit.verify()
    assert not ok and "Line 2" in message


def test_health_reports_ready():
    report = TestClient(webapp.app).get("/api/health").json()
    assert report["ok"] is True, report
