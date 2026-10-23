"""gateway v1.1: lesson 12's gateway + a job queue for slow questions.

New in this version:
  POST /jobs        put a question in the queue, answer at once with a job ID  (202 Accepted)
  GET  /jobs/{id}   ask "is my job done yet?"                                 (polling)
  GET  /queue       how many jobs are waiting
The slow work itself is done by a separate worker process (../worker/worker.py).
"""
import json
import os
import socket
import time
import uuid

import httpx
import redis
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel

RAG_URL = os.getenv("RAG_URL", "http://localhost:8001")
LLM_URL = os.getenv("LLM_URL", "http://localhost:8002")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

QUEUE = "queue:jobs"  # the Redis list that holds waiting job IDs
JOB_TTL_SECONDS = 3600  # Redis deletes finished job records after 1 hour

app = FastAPI(title="gateway")
http = httpx.Client(timeout=30.0)
# decode_responses=True: give us normal Python strings instead of raw bytes.
store = redis.Redis.from_url(REDIS_URL, decode_responses=True)


class AskRequest(BaseModel):
    question: str


def call_service(name: str, url: str, payload: dict, request_id: str) -> dict:
    try:
        r = http.post(url, json=payload, headers={"X-Request-ID": request_id})
        r.raise_for_status()
        return r.json()
    except httpx.HTTPError as e:
        raise HTTPException(status_code=502, detail=f"{name} failed: {e.__class__.__name__}: {e}")


@app.get("/health")
def health():
    return {"status": "ok", "service": "gateway", "version": "1.1", "host": socket.gethostname()}


@app.get("/health/deps")
def health_deps():
    result = {}
    for name, url in {"rag-service": RAG_URL, "llm-service": LLM_URL}.items():
        try:
            result[name] = http.get(f"{url}/health", timeout=2.0).json()
        except httpx.HTTPError as e:
            result[name] = {"status": "unreachable", "error": e.__class__.__name__}
    try:
        result["redis"] = {"status": "ok" if store.ping() else "error"}
    except redis.RedisError as e:
        result["redis"] = {"status": "unreachable", "error": e.__class__.__name__}
    return result


@app.post("/ask")
def ask(req: AskRequest, request: Request):
    """The old, synchronous way: you wait on the line until the answer is ready."""
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


@app.post("/jobs", status_code=202)
def create_job(req: AskRequest):
    """The new, asynchronous way: take a ticket, come back later."""
    job_id = uuid.uuid4().hex[:12]
    key = f"job:{job_id}"
    # A Redis "hash" is like a small dictionary stored under one key.
    store.hset(key, mapping={"id": job_id, "status": "queued", "question": req.question, "created_at": time.time()})
    store.expire(key, JOB_TTL_SECONDS)
    store.lpush(QUEUE, job_id)  # add the ticket to the LEFT end of the queue; workers take from the right
    return {"job_id": job_id, "status": "queued", "status_url": f"/jobs/{job_id}"}


@app.get("/jobs/{job_id}")
def get_job(job_id: str):
    job = store.hgetall(f"job:{job_id}")  # {} if the key does not exist
    if not job:
        raise HTTPException(status_code=404, detail="no such job (wrong ID, or it expired)")
    if "sources" in job:
        job["sources"] = json.loads(job["sources"])  # stored as JSON text, turn back into a list
    return job


@app.get("/queue")
def queue_length():
    return {"waiting": store.llen(QUEUE)}
