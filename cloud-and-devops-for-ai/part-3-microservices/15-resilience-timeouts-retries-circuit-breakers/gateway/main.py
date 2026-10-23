"""gateway v1.2: lesson 13's gateway, made tough.

New in this version:
  - timeouts:  never wait forever for rag-service or llm-service
  - retries:   try again (with backoff + jitter) when a call fails in a way that might be temporary
  - circuit breakers: stop hammering a service that is clearly down; fail fast instead
  - fallback:  if the LLM is down, still answer with the matching documents ("degraded" answer)
  - idempotency keys: sending the same POST /jobs twice creates only ONE job
"""
import json
import logging
import os
import socket
import time
import uuid

import httpx
import redis
from fastapi import FastAPI, Header, HTTPException, Request, Response
from pydantic import BaseModel

from resilience import CircuitBreaker, CircuitOpenError, retry_call

RAG_URL = os.getenv("RAG_URL", "http://localhost:8001")
LLM_URL = os.getenv("LLM_URL", "http://localhost:8002")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
# How long to wait for an answer (seconds). Search is quick; the LLM is allowed longer.
RAG_TIMEOUT = float(os.getenv("RAG_TIMEOUT", "2"))
LLM_TIMEOUT = float(os.getenv("LLM_TIMEOUT", "8"))
RETRY_ATTEMPTS = int(os.getenv("RETRY_ATTEMPTS", "3"))

QUEUE = "queue:jobs"
JOB_TTL_SECONDS = 3600
IDEMPOTENCY_TTL_SECONDS = 24 * 3600  # remember idempotency keys for one day

logging.basicConfig(level=logging.INFO, format="%(asctime)s gateway %(message)s")
log = logging.getLogger("gateway")

app = FastAPI(title="gateway")
http = httpx.Client(timeout=httpx.Timeout(10.0, connect=1.0))  # default; each call below sets its own
store = redis.Redis.from_url(REDIS_URL, decode_responses=True)

class RetryableError(Exception):
    """A failure that might go away if we try again (network trouble, timeouts, 5xx errors)."""


# One breaker per service. 3 sick answers in a row -> open for 15 s. Only RetryableErrors count.
breakers = {
    "rag-service": CircuitBreaker("rag-service", failure_threshold=3, reset_after=15, failure_on=(RetryableError,)),
    "llm-service": CircuitBreaker("llm-service", failure_threshold=3, reset_after=15, failure_on=(RetryableError,)),
}


class AskRequest(BaseModel):
    question: str


def post_json(url: str, payload: dict, timeout: float, request_id: str) -> dict:
    """ONE attempt. Sorts failures into 'worth retrying' and 'not worth retrying'."""
    try:
        # read timeout = `timeout` seconds; connect timeout = 1 s (if nobody picks up, it's probably down)
        r = http.post(url, json=payload, timeout=httpx.Timeout(timeout, connect=1.0), headers={"X-Request-ID": request_id})
    except httpx.TransportError as e:  # could not connect, connection dropped, timed out ...
        raise RetryableError(f"{e.__class__.__name__}") from e
    if r.status_code >= 500:  # the other service had a problem; maybe it's temporary
        raise RetryableError(f"HTTP {r.status_code}")
    r.raise_for_status()  # 4xx = OUR request is wrong; retrying won't help, so this is not retried
    return r.json()


def call_service(name: str, url: str, payload: dict, timeout: float, request_id: str) -> dict:
    """Circuit breaker around retries around one attempt with a timeout."""

    def log_retry(attempt, delay, error):
        log.info("[%s] %s attempt %d failed (%s), retrying in %.2fs", request_id, name, attempt, error, delay)

    def with_retries():
        return retry_call(
            lambda: post_json(url, payload, timeout, request_id),
            attempts=RETRY_ATTEMPTS,
            base=0.2,
            cap=2.0,
            retry_on=(RetryableError,),
            on_retry=log_retry,
        )

    return breakers[name].call(with_retries)


@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "gateway",
        "version": "1.2",
        "host": socket.gethostname(),
        "breakers": {name: b.status() for name, b in breakers.items()},
    }


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
    request_id = request.headers.get("X-Request-ID") or uuid.uuid4().hex[:12]
    t0 = time.perf_counter()

    # Step 1: search. Without documents we can't do anything useful, so failures here are a 503.
    try:
        found = call_service("rag-service", f"{RAG_URL}/search", {"question": req.question}, RAG_TIMEOUT, request_id)
    except (RetryableError, CircuitOpenError) as e:
        raise HTTPException(status_code=503, detail=f"search is unavailable right now ({e})")
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=502, detail=f"rag-service refused the request: {e.response.status_code}")
    docs = found["results"]
    t1 = time.perf_counter()

    # Step 2: the LLM. If it fails, fall back to a "degraded" answer instead of an error.
    degraded = False
    try:
        reply = call_service(
            "llm-service",
            f"{LLM_URL}/generate",
            {"question": req.question, "context": [d["text"] for d in docs]},
            LLM_TIMEOUT,
            request_id,
        )
        answer, model = reply["answer"], reply["model"]
    except (RetryableError, CircuitOpenError, httpx.HTTPStatusError) as e:
        log.info("[%s] llm-service unavailable (%s), sending degraded answer", request_id, e)
        degraded, model = True, None
        if docs:
            answer = "The AI helper is unavailable right now. These documents look relevant: " + " | ".join(d["text"] for d in docs)
        else:
            answer = "The AI helper is unavailable right now, and no documents matched your question."
    t2 = time.perf_counter()

    return {
        "question": req.question,
        "answer": answer,
        "sources": [d["title"] for d in docs],
        "model": model,
        "degraded": degraded,
        "request_id": request_id,
        "timings_ms": {"rag": round((t1 - t0) * 1000), "llm": round((t2 - t1) * 1000)},
    }


@app.post("/jobs", status_code=202)
def create_job(req: AskRequest, response: Response, idempotency_key: str | None = Header(default=None)):
    """Like lesson 13, plus an optional 'Idempotency-Key' header.

    Same key again (say the client retried because its network dropped) -> same job, not a new one.
    """
    job_id = uuid.uuid4().hex[:12]
    if idempotency_key:
        # SET ... NX = only set it if the key does NOT exist yet. Redis does this in one atomic step,
        # so two identical requests arriving at the same moment can't both win.
        first_time = store.set(f"idem:{idempotency_key}", job_id, nx=True, ex=IDEMPOTENCY_TTL_SECONDS)
        if not first_time:
            existing_id = store.get(f"idem:{idempotency_key}")
            response.status_code = 200
            response.headers["Idempotent-Replay"] = "true"
            job = store.hgetall(f"job:{existing_id}")
            return {"job_id": existing_id, "status": job.get("status", "unknown"), "status_url": f"/jobs/{existing_id}"}

    key = f"job:{job_id}"
    store.hset(key, mapping={"id": job_id, "status": "queued", "question": req.question, "created_at": time.time()})
    store.expire(key, JOB_TTL_SECONDS)
    store.lpush(QUEUE, job_id)
    return {"job_id": job_id, "status": "queued", "status_url": f"/jobs/{job_id}"}


@app.get("/jobs/{job_id}")
def get_job(job_id: str):
    job = store.hgetall(f"job:{job_id}")
    if not job:
        raise HTTPException(status_code=404, detail="no such job (wrong ID, or it expired)")
    if "sources" in job:
        job["sources"] = json.loads(job["sources"])
    return job


@app.get("/queue")
def queue_length():
    return {"waiting": store.llen(QUEUE)}
