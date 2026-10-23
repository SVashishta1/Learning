"""gateway: the front door. The only service the outside world talks to.

For each question it asks rag-service for documents, then asks llm-service for an answer.
Run alone:  uvicorn main:app --port 8000   (expects rag-service on 8001 and llm-service on 8002)
"""
import os
import socket
import time
import uuid

import httpx
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel

# Where the other services live. In Docker Compose these become http://rag-service:8000 etc.
RAG_URL = os.getenv("RAG_URL", "http://localhost:8001")
LLM_URL = os.getenv("LLM_URL", "http://localhost:8002")

app = FastAPI(title="gateway")
# One shared HTTP client: it re-uses connections, which is faster than opening a new one each time.
http = httpx.Client(timeout=30.0)


class AskRequest(BaseModel):
    question: str


def call_service(name: str, url: str, payload: dict, request_id: str) -> dict:
    """POST to another service and return its JSON, or fail with a clear 502 error."""
    try:
        r = http.post(url, json=payload, headers={"X-Request-ID": request_id})
        r.raise_for_status()  # turns 4xx/5xx answers into an exception
        return r.json()
    except httpx.HTTPError as e:
        raise HTTPException(status_code=502, detail=f"{name} failed: {e.__class__.__name__}: {e}")


@app.get("/health")
def health():
    return {"status": "ok", "service": "gateway", "host": socket.gethostname()}


@app.get("/health/deps")
def health_deps():
    """Can the gateway reach the services it depends on?"""
    result = {}
    for name, url in {"rag-service": RAG_URL, "llm-service": LLM_URL}.items():
        try:
            result[name] = http.get(f"{url}/health", timeout=2.0).json()
        except httpx.HTTPError as e:
            result[name] = {"status": "unreachable", "error": e.__class__.__name__}
    return result


@app.post("/ask")
def ask(req: AskRequest, request: Request):
    # A "request ID" follows one question through every service, so you can match up their logs.
    request_id = request.headers.get("X-Request-ID") or uuid.uuid4().hex[:12]

    t0 = time.perf_counter()
    found = call_service("rag-service", f"{RAG_URL}/search", {"question": req.question}, request_id)
    t1 = time.perf_counter()
    context = [doc["text"] for doc in found["results"]]
    reply = call_service("llm-service", f"{LLM_URL}/generate", {"question": req.question, "context": context}, request_id)
    t2 = time.perf_counter()

    return {
        "question": req.question,
        "answer": reply["answer"],
        "sources": [doc["title"] for doc in found["results"]],
        "model": reply["model"],
        "request_id": request_id,
        "timings_ms": {"rag": round((t1 - t0) * 1000), "llm": round((t2 - t1) * 1000)},
    }
