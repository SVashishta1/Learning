"""app.py: the claims desk web API and page.   FAKE_LLM=1 uvicorn app:app --port 8000

    POST /api/runs                         process the claims queue in the background -> {"id": ...}
    GET  /api/runs/{id}                    batch report, claims, assessments, drafts, actions, trace
    POST /api/runs/{id}/actions/{aid}      {"approve": true, "by": "Priya", "role": "handler" | "supervisor"}
    POST /api/runs/{id}/execute            pays and sends ONLY approved actions (through the Northwind API)
    GET  /api/outbox                       what the (mock) Northwind systems received
In production the role comes from single sign-on (lesson 08), not from the request body.
"""
import threading
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

import llm
from team import decide, new_run, run_desk

HERE = Path(__file__).parent
app = FastAPI(title="Northwind AI claims desk")
RUNS = {}


class Approval(BaseModel):
    approve: bool
    by: str
    role: Literal["handler", "supervisor"] = "handler"


@app.get("/")
def page():
    return FileResponse(HERE / "static" / "index.html")


@app.get("/healthz")
def health():
    return {"ok": True}


@app.get("/api/info")
def info():
    return {"provider": llm.provider_name()}


@app.post("/api/runs")
def start():
    try:
        provider = llm.get_provider()
    except SystemExit as e:
        raise HTTPException(400, str(e))
    m = new_run()
    RUNS[m.id] = m
    threading.Thread(target=run_desk, kwargs={"mission": m, "provider": provider}, daemon=True).start()
    return {"id": m.id, "tickets": len(m.state["new_tickets"])}


def _get(rid):
    if rid not in RUNS:
        raise HTTPException(404, "No such run")
    return RUNS[rid]


@app.get("/api/runs/{rid}")
def get_run(rid: str):
    m = _get(rid)
    d = m.state["desk"]
    return {**m.to_dict(), "claims": list(d.claims.values()), "assessments": d.assessments, "drafts": d.drafts,
            "policy_basis": d.policy_basis}


@app.post("/api/runs/{rid}/actions/{aid}")
def approve(rid: str, aid: str, a: Approval):
    try:
        return decide(_get(rid), aid, a.approve, a.by, a.role).model_dump()
    except PermissionError as e:
        raise HTTPException(403, str(e))
    except (KeyError, ValueError) as e:
        raise HTTPException(400, str(e))


@app.post("/api/runs/{rid}/execute")
def execute(rid: str):
    return [a.model_dump() for a in _get(rid).execute_approved()]


@app.get("/api/outbox")
def outbox():
    m = next(reversed(RUNS.values()), None)
    if m is None:
        return {}
    return m.state["desk"].client.request("GET", "/admin/outbox")
