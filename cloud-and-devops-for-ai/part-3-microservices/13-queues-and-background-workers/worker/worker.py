"""worker: takes jobs from the Redis queue and does the slow work (search + LLM).

It is not a web server. It is a loop that never ends:
  wait for a job -> mark it "running" -> do the work -> save the answer as "done" (or "failed")
Run:  python worker.py
"""
import json
import os
import signal
import socket
import time

import httpx
import redis

RAG_URL = os.getenv("RAG_URL", "http://localhost:8001")
LLM_URL = os.getenv("LLM_URL", "http://localhost:8002")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
QUEUE = "queue:jobs"
WORKER_NAME = os.getenv("WORKER_NAME", socket.gethostname())  # so you can see WHICH worker did a job

store = redis.Redis.from_url(REDIS_URL, decode_responses=True)
http = httpx.Client(timeout=120.0)  # workers can afford to wait longer than a web request
running = True


def stop(signum, frame):
    """Docker sends SIGTERM on 'docker compose stop'. Finish the current job, then exit."""
    global running
    print(f"[{WORKER_NAME}] got signal {signum}, finishing current job then stopping", flush=True)
    running = False


signal.signal(signal.SIGTERM, stop)
signal.signal(signal.SIGINT, stop)  # Ctrl + C


def process(job_id: str) -> None:
    key = f"job:{job_id}"
    question = store.hget(key, "question")
    if question is None:
        print(f"[{WORKER_NAME}] job {job_id} has no record (expired?), skipping", flush=True)
        return
    store.hset(key, mapping={"status": "running", "worker": WORKER_NAME, "started_at": time.time()})
    print(f"[{WORKER_NAME}] job {job_id} running: {question!r}", flush=True)
    try:
        r = http.post(f"{RAG_URL}/search", json={"question": question}, headers={"X-Request-ID": job_id})
        r.raise_for_status()
        docs = r.json()["results"]
        r = http.post(
            f"{LLM_URL}/generate",
            json={"question": question, "context": [d["text"] for d in docs]},
            headers={"X-Request-ID": job_id},
        )
        r.raise_for_status()
        reply = r.json()
        store.hset(key, mapping={
            "status": "done",
            "answer": reply["answer"],
            "model": reply["model"],
            "sources": json.dumps([d["title"] for d in docs]),  # Redis stores text, so save the list as JSON
            "finished_at": time.time(),
        })
        print(f"[{WORKER_NAME}] job {job_id} done", flush=True)
    except (httpx.HTTPError, KeyError, ValueError) as e:
        store.hset(key, mapping={"status": "failed", "error": f"{e.__class__.__name__}: {e}", "finished_at": time.time()})
        print(f"[{WORKER_NAME}] job {job_id} FAILED: {e}", flush=True)


def main() -> None:
    print(f"[{WORKER_NAME}] waiting for jobs on '{QUEUE}' at {REDIS_URL}", flush=True)
    while running:
        try:
            # BRPOP = "Blocking Right POP": wait up to 5 s for a job to appear, then take it from the right end.
            item = store.brpop([QUEUE], timeout=5)
        except redis.TimeoutError:
            continue  # the wait was interrupted (for example by a stop signal); loop and check `running`
        except redis.ConnectionError:
            print(f"[{WORKER_NAME}] cannot reach Redis, retrying in 2 s", flush=True)
            time.sleep(2)
            continue
        if item is None:
            continue  # no job in 5 s; loop again (and notice if we were asked to stop)
        _queue_name, job_id = item
        process(job_id)
    print(f"[{WORKER_NAME}] stopped cleanly", flush=True)


if __name__ == "__main__":
    main()
