import json
import time

import pytest
from fastapi.testclient import TestClient

import app as demo
import llm
import preflight
from fake_llm import FakeClaude

client = TestClient(demo.app)
SAMPLE = {s["id"]: s for s in demo.SAMPLES}


@pytest.fixture
def live(monkeypatch):
    """Live mode with a fake Claude that returns a fixed, valid triage."""
    fake = FakeClaude(parsed=demo.Triage(**demo.RECORDED["delayed"]))
    monkeypatch.setattr(demo, "DEMO_MODE", "live")
    monkeypatch.setattr(llm, "PROVIDER", "anthropic")
    monkeypatch.setattr(llm, "_client", fake)
    return fake


def test_page_and_samples_are_served():
    assert "Northwind Reply Assistant" in client.get("/").text
    assert len(client.get("/api/samples").json()) == 4


def test_facts_come_from_code_not_ai():
    tracking, shipment = demo.find_facts(SAMPLE["delayed"]["email"])
    assert tracking == "NW-4821907" and shipment["status"] == "delayed"
    assert demo.find_facts(SAMPLE["no-number"]["email"]) == (None, None)


def test_live_draft_sends_record_and_policy(live):
    result = client.post("/api/draft", json={"email": SAMPLE["delayed"]["email"], "sample_id": "delayed"}).json()
    assert result["mode"] == "live" and result["triage"]["category"] == "where_is_my_shipment"
    prompt = live.calls[0]["messages"][0]["content"]
    assert "vehicle breakdown" in prompt and "[DT-3.2]" in prompt     # the AI is given the facts and policy


def test_ai_failure_falls_back_to_recorded_and_says_so(live, monkeypatch):
    def broken(**kwargs):
        raise ConnectionError("network down")
    live.beta.messages.parse = broken
    result = client.post("/api/draft", json={"email": SAMPLE["damaged"]["email"], "sample_id": "damaged"}).json()
    assert result["mode"] == "fallback" and "ConnectionError" in result["note"]
    assert result["triage"]["category"] == "damage_claim"
    assert result["shipment"]["customer"] == "Hartmann GmbH"           # the lookup still works


def test_custom_email_without_ai_still_shows_facts(monkeypatch):
    monkeypatch.setattr(demo, "DEMO_MODE", "live")
    monkeypatch.setattr(llm, "PROVIDER", "anthropic")
    monkeypatch.setattr(llm, "_client", None)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)            # no key: the demo must not crash
    result = client.post("/api/draft", json={"email": "Where is NW-3310452?"}).json()
    assert result["mode"] == "unavailable" and result["triage"] is None
    assert result["shipment"]["status"] == "delivered"


def test_slow_ai_times_out(live, monkeypatch):
    def slow(**kwargs):
        time.sleep(0.5)
    live.beta.messages.parse = slow
    monkeypatch.setattr(demo, "TIMEOUT", 0.1)
    result = client.post("/api/draft", json={"email": SAMPLE["delayed"]["email"], "sample_id": "delayed"}).json()
    assert result["mode"] == "fallback" and "timed out" in result["note"]


def test_recorded_mode_needs_no_ai(monkeypatch):
    monkeypatch.setattr(demo, "DEMO_MODE", "recorded")
    result = client.post("/api/draft", json={"email": "x", "sample_id": "no-number"}).json()
    assert result["mode"] == "recorded" and "tracking number" in result["triage"]["draft_reply"]


def test_empty_email_is_rejected():
    assert client.post("/api/draft", json={"email": ""}).status_code == 422


def test_every_recorded_answer_fits_the_form():
    for answer in demo.RECORDED.values():
        demo.Triage(**answer)                                           # raises if a field is wrong


def test_preflight_reports_fallbacks(live):
    live.beta.messages.parse = lambda **kwargs: (_ for _ in ()).throw(RuntimeError("down"))
    problems, lines = preflight.check("http://testserver", client=client)
    assert any("live AI failed" in p for p in problems)
    assert lines[0].startswith("App is up")
