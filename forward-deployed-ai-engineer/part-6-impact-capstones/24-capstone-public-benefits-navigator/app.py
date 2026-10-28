"""app.py: the navigator's web API and page.  Run:  FAKE_LLM=1 uvicorn app:app --port 8000

    POST /api/sessions                        {"story": "...", "known_names": ["Maria Lopez"]} -> starts the team
    GET  /api/sessions/{id}                   plan, explanation, checklist, forms (placeholders only), trace
    GET  /api/sessions/{id}/forms/{programme} the form with personal details put back (stays on this server)
    POST /api/sessions/{id}/actions/{aid}     {"approve": true, "by": "Aisha + caseworker Ben"}
    POST /api/sessions/{id}/execute           submits ONLY approved forms (simulated)
"""
import os
import threading
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

import llm
from team import get_private_provider, new_session, run_navigator

HERE = Path(__file__).parent
app = FastAPI(title="Benefits navigator (fictional policies)")
SESSIONS = {}


class StartRequest(BaseModel):
    story: str
    known_names: list[str] = []


class Decision(BaseModel):
    approve: bool
    by: str
    note: str = ""


@app.get("/")
def page():
    return FileResponse(HERE / "static" / "index.html")


@app.get("/healthz")
def health():
    return {"ok": True}


@app.get("/api/info")
def info():
    return {"provider": llm.provider_name(), "require_local_model": os.getenv("REQUIRE_LOCAL_MODEL") == "1"}


@app.post("/api/sessions")
def start(req: StartRequest):
    if len(req.story.strip()) < 20:
        raise HTTPException(400, "Tell us a little more about your household (who lives with you, income, rent).")
    try:
        provider = get_private_provider()
    except SystemExit as e:
        raise HTTPException(400, str(e))
    m = new_session(req.story, req.known_names)
    SESSIONS[m.id] = m
    threading.Thread(target=run_navigator, kwargs={"mission": m, "provider": provider}, daemon=True).start()
    return {"id": m.id}


def _get(sid):
    if sid not in SESSIONS:
        raise HTTPException(404, "No such session")
    return SESSIONS[sid]


@app.get("/api/sessions/{sid}")
def get_session(sid: str):
    m = _get(sid)
    s = m.state
    checklist = ((m.reports.get("documents") or {}).get("report") or {}).get("checklist", [])
    return {**m.to_dict(), "story_redacted": s["story_redacted"],
            "profile": s["profile"].model_dump() if s["profile"] else None,
            "rules": s["rules"], "explanation": s["explanation"], "checklist": checklist,
            "forms": s["forms"], "submitted_count": len(s["submitted"])}


@app.get("/api/sessions/{sid}/forms/{programme}")
def reveal_form(sid: str, programme: str):
    m = _get(sid)
    form = m.state["forms"].get(programme)
    if form is None:
        raise HTTPException(404, "No draft for this programme")
    return {k: m.state["vault"].restore(v) for k, v in form.items()}


@app.post("/api/sessions/{sid}/actions/{aid}")
def decide(sid: str, aid: str, d: Decision):
    try:
        return _get(sid).decide(aid, d.approve, d.by, d.note).model_dump()
    except (KeyError, ValueError) as e:
        raise HTTPException(400, str(e))


@app.post("/api/sessions/{sid}/execute")
def execute(sid: str):
    return [a.model_dump() for a in _get(sid).execute_approved()]
