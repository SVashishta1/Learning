# app.py: the Northwind Reply Assistant demo. Paste a customer email, get the shipment facts and a draft reply.
#
#   uvicorn app:app --reload                         (live AI: Claude, or Ollama with LLM_PROVIDER=ollama)
#   DEMO_MODE=recorded uvicorn app:app               (no AI at all: recorded answers, for bad Wi-Fi days)
#
# Demo rules built into the code:
#   1. Facts (tracking number, shipment status) come from code and data, never from the AI.
#   2. If the live AI fails or is slow, the demo falls back to a recorded answer and SAYS so on screen.
import asyncio
import json
import os
import re
import time
from pathlib import Path
from typing import Literal, Optional

from fastapi import FastAPI
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

import llm

HERE = Path(__file__).parent
SAMPLES = json.loads((HERE / "samples.json").read_text(encoding="utf-8"))
SHIPMENTS = json.loads((HERE / "shipments.json").read_text(encoding="utf-8"))    # a tiny stand-in for the TMS
RECORDED = json.loads((HERE / "recorded.json").read_text(encoding="utf-8"))      # answers saved from a good run
POLICY = (HERE / "policy.md").read_text(encoding="utf-8")
DEMO_MODE = os.getenv("DEMO_MODE", "live")              # "live" or "recorded"
TIMEOUT = float(os.getenv("DEMO_TIMEOUT", "20"))        # seconds before we give up on the live AI
TRACKING = re.compile(r"\bNW-\d{7}\b")                  # Northwind tracking numbers look like NW-1234567


class Triage(BaseModel):
    """The form the AI fills in for every email."""
    category: Literal["where_is_my_shipment", "damage_claim", "invoice", "other"]
    urgency: Literal["low", "medium", "high"]
    summary: str = Field(description="one sentence: what the customer wants")
    draft_reply: str = Field(description="the reply for the agent to review, signed 'Northwind Customer Support'")
    cited_clauses: list[str] = Field(description="policy clause ids used, e.g. ['DT-3.1']")


class DraftRequest(BaseModel):
    email: str = Field(min_length=1, max_length=5000)
    sample_id: Optional[str] = None                      # set when the email came from a sample button


SYSTEM = """You help Northwind Logistics support agents. You draft replies that an agent reviews before sending.
Rules:
- Use ONLY the shipment record and the policy clauses given. Never invent dates, names, amounts or promises.
- Cite every policy clause you rely on by its id, e.g. DT-3.1.
- Damage claims and invoice questions are not handled by Support: draft a short reply saying the request has been
  passed to the right team (cite DT-5.1 for damage).
- If there is no shipment record, ask the customer for their tracking number (format NW-1234567).
- Be warm, brief and specific. Sign as 'Northwind Customer Support'."""


def find_facts(email):
    """Pull the tracking number out with a pattern and look it up. Code does this, not the AI."""
    match = TRACKING.search(email)
    tracking = match.group(0) if match else None
    return tracking, SHIPMENTS.get(tracking) if tracking else None


def build_prompt(email, tracking, shipment):
    record = json.dumps(shipment, ensure_ascii=False) if shipment else "NO RECORD FOUND"
    return (f"<email>\n{email}\n</email>\n\n<shipment_record tracking=\"{tracking or 'none'}\">\n{record}\n"
            f"</shipment_record>\n\n<policy>\n{POLICY}\n</policy>")


def live_triage(prompt):
    """Call the AI. Turn 'no key' into a normal error so the demo can fall back instead of stopping."""
    try:
        return llm.ask_json(prompt, Triage, system=SYSTEM, max_tokens=1500)
    except SystemExit as problem:
        raise RuntimeError(str(problem)) from None


app = FastAPI(title="Northwind Reply Assistant (demo)")


@app.get("/")
def home():
    return FileResponse(HERE / "static" / "index.html")


@app.get("/api/samples")
def samples():
    return SAMPLES


@app.get("/api/health")
def health():
    """Used by preflight.py before the demo: is everything configured the way we think?"""
    return {"status": "ok", "demo_mode": DEMO_MODE, "provider": llm.PROVIDER, "model": llm.model_name(),
            "timeout_seconds": TIMEOUT, "samples": len(SAMPLES), "recorded": sorted(RECORDED)}


@app.post("/api/draft")
async def draft(request: DraftRequest):
    started = time.perf_counter()
    tracking, shipment = find_facts(request.email)
    triage, mode, note = None, "live", None

    if DEMO_MODE == "recorded":
        mode = "recorded"
        triage = RECORDED.get(request.sample_id or "")
        note = "Recorded answer (demo mode)." if triage else "Recorded mode has no answer for custom emails."
    else:
        try:
            # Run the slow AI call in a helper thread, and stop waiting after TIMEOUT seconds.
            result = await asyncio.wait_for(asyncio.to_thread(live_triage, build_prompt(request.email, tracking,
                                                                                       shipment)), TIMEOUT)
            triage = result.model_dump()
        except Exception as problem:                       # timeout, no key, network down, bad JSON...
            reason = ("timed out" if isinstance(problem, TimeoutError)
                      else f"{type(problem).__name__}: {str(problem).split('. ')[0]}")   # first sentence only
            triage = RECORDED.get(request.sample_id or "")
            mode = "fallback" if triage else "unavailable"
            note = (f"Live AI unavailable ({reason}). Showing a recorded answer." if triage
                    else f"Live AI unavailable ({reason}). The shipment lookup above still works.")

    seconds = round(time.perf_counter() - started, 2)
    print(f"[draft] mode={mode} sample={request.sample_id} tracking={tracking} seconds={seconds}")
    return {"mode": mode, "note": note, "seconds": seconds, "tracking": tracking,
            "shipment": shipment, "triage": triage}
