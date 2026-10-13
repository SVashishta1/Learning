"""Project 7.6 capstone: a production-style 'Ask the handbook' AI service.

Features: RAG answers with citations · document upload · API-key auth · rate limiting · daily budget cap ·
JSON logs · Prometheus metrics · health/readiness checks · runs in Docker · CI tests with a fake LLM.
"""
import os
import shutil
import time
import uuid
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI, File, HTTPException, Request, UploadFile
from fastapi.responses import PlainTextResponse
from prometheus_client import generate_latest
from pydantic import BaseModel, Field

from app import llm
from app.observability import LATENCY, REQUESTS, get_logger, record_usage
from app.rag import Embedder, Index, answer
from app.security import add_spend, check_budget, require_api_key

DOCS_DIR = os.getenv("DOCS_DIR", "docs")
EMBEDDER = os.getenv("EMBEDDER", "auto")          # "tfidf" keeps the Docker image small
log = get_logger()
state: dict = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    state["index"] = Index(Embedder(EMBEDDER)).build(DOCS_DIR)
    state["client"] = state.get("client") or llm.get_client()
    log.info("ready", extra={"extra_fields": {"chunks": len(state["index"].chunks), "embedder": state["index"].embedder.backend}})
    yield


app = FastAPI(title="Handbook AI", lifespan=lifespan)


@app.middleware("http")
async def observe(request: Request, call_next):
    request_id = request.headers.get("x-request-id", uuid.uuid4().hex[:12])
    start = time.perf_counter()
    response = await call_next(request)
    elapsed = time.perf_counter() - start
    endpoint = request.url.path
    REQUESTS.labels(endpoint, str(response.status_code)).inc()
    LATENCY.labels(endpoint).observe(elapsed)
    response.headers["x-request-id"] = request_id
    log.info("request", extra={"extra_fields": {"id": request_id, "path": endpoint, "status": response.status_code, "ms": round(elapsed * 1000)}})
    return response


class Question(BaseModel):
    question: str = Field(min_length=3, max_length=1000)
    k: int = Field(4, ge=1, le=10)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/ready")
def ready():
    if "index" not in state:
        raise HTTPException(503, "starting up")
    return {"status": "ready", "chunks": len(state["index"].chunks)}


@app.get("/metrics", response_class=PlainTextResponse)
def metrics():
    return generate_latest()


@app.post("/ask")
def ask(q: Question, key: str = Depends(require_api_key)):
    check_budget()
    result = answer(state["client"], state["index"], q.question, q.k)
    usage = result["usage"]
    add_spend(record_usage(llm.MODEL, usage["input_tokens"], usage["output_tokens"]))
    log.info("answer", extra={"extra_fields": {"key": key[:4] + "…", "question_chars": len(q.question), "cited": len(result["sources"])}})
    return result


@app.post("/documents", status_code=201)
async def upload(file: UploadFile = File(...), key: str = Depends(require_api_key)):
    name = Path(file.filename or "").name
    if Path(name).suffix.lower() not in {".pdf", ".md", ".txt"}:
        raise HTTPException(400, "Only .pdf, .md and .txt files are accepted")
    with (Path(DOCS_DIR) / name).open("wb") as f:
        shutil.copyfileobj(file.file, f)
    state["index"] = Index(Embedder(EMBEDDER)).build(DOCS_DIR)
    return {"added": name, "chunks": len(state["index"].chunks)}
