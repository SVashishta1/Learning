"""app.py: the small service we deploy in this lesson (a Northwind support helper).

    GET  /healthz   "is the process alive?"        (load balancer / Docker / Kubernetes liveness)
    GET  /ready     "can it do its job?"            (config and secrets present, brain created)
    POST /ask       {"question": "..."} -> {"answer": "...", "provider": "..."}
Run:  LLM_PROVIDER=fake uvicorn app:app --port 8000
"""
import logging
import os

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from providers import get_brain

logging.basicConfig(level=logging.INFO, format='{"level":"%(levelname)s","msg":"%(message)s"}')   # JSON-ish logs
log = logging.getLogger("assistant")
app = FastAPI(title="Northwind assistant")
_brain = None


class Question(BaseModel):
    question: str = Field(min_length=3, max_length=4000)


def brain():
    global _brain
    if _brain is None:
        _brain = get_brain()
    return _brain


@app.get("/healthz")
def healthz():
    return {"ok": True}


@app.get("/ready")
def ready():
    try:
        b = brain()
    except Exception as e:                          # missing secret, wrong config: not ready, but alive
        raise HTTPException(503, f"not ready: {e}")
    return {"ready": True, "provider": b.name, "model": b.model, "region": os.getenv("AWS_REGION") or os.getenv("GCP_REGION")}


@app.post("/ask")
def ask(q: Question):
    b = brain()
    answer = b.ask(q.question)
    log.info("answered provider=%s question_chars=%d", b.name, len(q.question))   # never log the text itself
    return {"answer": answer, "provider": b.name}
