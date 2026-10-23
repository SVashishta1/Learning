"""app.py: the command center's web API and page.  Run:  FAKE_LLM=1 uvicorn app:app --port 8000

    GET  /                                  the web page (static/index.html)
    GET  /api/info                          which brain is in use (fake, anthropic, ollama)
    GET  /api/scenarios                     the practice scenarios
    POST /api/missions                      {"scenario": "baseline"} -> starts the team in the background
    GET  /api/missions/{id}                 everything: status, plan, actions, reports, trace, map
    POST /api/missions/{id}/actions/{aid}   {"approve": true, "by": "Sam"} -> a human decision
    POST /api/missions/{id}/execute         runs ONLY the approved actions
"""
import json
import threading
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

import llm
from agent_core import Budget
from team import new_mission, run_relief_mission

HERE = Path(__file__).parent
SCENARIOS = json.loads((HERE / "data" / "scenarios.json").read_text(encoding="utf-8"))
app = FastAPI(title="Marrow Valley relief command center")
MISSIONS = {}                       # in memory: fine for a demo; use a database for real (see README)


class StartRequest(BaseModel):
    scenario: str = "baseline"
    max_usd: float = 1.0


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
    name = llm.provider_name()
    models = {"fake": "rule-based stand-ins", "anthropic": f"{llm.HEAD_MODEL} (head) + {llm.SPECIALIST_MODEL} (specialists)"}
    return {"provider": name, "models": models.get(name, f"{llm.OLLAMA_HEAD_MODEL} / {llm.OLLAMA_MODEL} at {llm.OLLAMA_BASE_URL}")}


@app.get("/api/scenarios")
def scenarios():
    return {k: v["description"] for k, v in SCENARIOS.items()}


@app.post("/api/missions")
def start(req: StartRequest):
    if req.scenario not in SCENARIOS:
        raise HTTPException(404, f"Unknown scenario {req.scenario}")
    try:
        provider = llm.get_provider()
    except SystemExit as e:                                  # e.g. no API key
        raise HTTPException(400, str(e))
    mission = new_mission(SCENARIOS[req.scenario]["scenario"], Budget(max_usd=req.max_usd))
    MISSIONS[mission.id] = mission
    threading.Thread(target=run_relief_mission, kwargs={"mission": mission, "provider": provider}, daemon=True).start()
    return {"id": mission.id}


def _get(mission_id: str):
    if mission_id not in MISSIONS:
        raise HTTPException(404, "No such mission")
    return MISSIONS[mission_id]


@app.get("/api/missions/{mission_id}")
def get_mission(mission_id: str):
    m = _get(mission_id)
    world = m.state["world"]
    return {**m.to_dict(), "incidents": list(world.incidents.values()), "drafts": list(world.drafts.values()),
            "outbox": world.outbox, "map": world.map_data(m.actions),
            "stock": {k: v["stock"] for k, v in world.items.items()}}


@app.post("/api/missions/{mission_id}/actions/{action_id}")
def decide(mission_id: str, action_id: str, d: Decision):
    m = _get(mission_id)
    try:
        return m.decide(action_id, d.approve, d.by, d.note).model_dump()
    except (KeyError, ValueError) as e:
        raise HTTPException(400, str(e))


@app.post("/api/missions/{mission_id}/execute")
def execute(mission_id: str):
    m = _get(mission_id)
    return [a.model_dump() for a in m.execute_approved()]
