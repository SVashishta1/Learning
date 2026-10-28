"""End to end in FAKE mode: the team, privacy, evals, the web API and voice intake (with a stub Whisper)."""
import sys
import time
import types

import pytest
from fastapi.testclient import TestClient

from app import app
from evals.run_evals import run
from llm import FakeProvider
from privacy import find_leaks
from team import EXAMPLE, get_private_provider, run_navigator


def test_full_session_never_shows_pii_to_the_model_and_submits_only_after_approval():
    provider = FakeProvider()
    m = run_navigator(EXAMPLE, provider=provider)
    assert m.status == "awaiting_approval"
    sent = " ".join(x["system"] + x["messages"] for x in provider.sent)
    assert "Aisha" not in sent and "07700" not in sent and find_leaks(sent, m.state["vault"]) == []
    fb = next(a for a in m.actions if a.args["programme"] == "foodbridge")
    m.decide(fb.id, True, by="Aisha and caseworker Ben")
    m.execute_approved()
    assert m.state["submitted"][0]["values"]["applicant_name"] == "Aisha Khan"     # restored locally only


def test_golden_households():
    for row in run():
        assert all(row["checks"].values()), (row["id"], [k for k, v in row["checks"].items() if not v])


def test_require_local_model_refuses_the_cloud(monkeypatch):
    monkeypatch.setenv("FAKE_LLM", "0")
    monkeypatch.setenv("LLM_PROVIDER", "anthropic")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test")
    monkeypatch.setenv("REQUIRE_LOCAL_MODEL", "1")
    with pytest.raises(SystemExit, match="REQUIRE_LOCAL_MODEL"):
        get_private_provider()


def test_web_api():
    c = TestClient(app)
    assert "Benefits navigator" in c.get("/").text
    assert c.post("/api/sessions", json={"story": "help"}).status_code == 400
    sid = c.post("/api/sessions", json={"story": EXAMPLE, "known_names": ["Zara"]}).json()["id"]
    for _ in range(50):
        s = c.get(f"/api/sessions/{sid}").json()
        if s["status"] not in ("created", "running"):
            break
        time.sleep(0.1)
    assert s["status"] == "awaiting_approval" and "Aisha" not in s["story_redacted"]
    assert "[NAME_2]" in str(s["forms"]) and "Aisha" not in str(s["forms"])
    assert c.get(f"/api/sessions/{sid}/forms/foodbridge").json()["applicant_name"] == "Aisha Khan"
    aid = s["actions"][0]["id"]
    c.post(f"/api/sessions/{sid}/actions/{aid}", json={"approve": True, "by": "Aisha + Ben"})
    assert c.post(f"/api/sessions/{sid}/execute").json()[0]["status"] == "executed"


def test_voice_intake_with_a_stub_whisper(monkeypatch, tmp_path, capsys):
    seg = types.SimpleNamespace(text=" Somos 3 en Brightwater. ")
    fake = types.ModuleType("faster_whisper")
    fake.WhisperModel = lambda *a, **k: types.SimpleNamespace(
        transcribe=lambda path: ([seg], types.SimpleNamespace(language="es")))
    monkeypatch.setitem(sys.modules, "faster_whisper", fake)
    wav = tmp_path / "story.wav"
    wav.write_bytes(b"RIFF")
    import voice_intake
    assert voice_intake.main([str(wav)]) == "Somos 3 en Brightwater."
    assert "[es]" in capsys.readouterr().out
