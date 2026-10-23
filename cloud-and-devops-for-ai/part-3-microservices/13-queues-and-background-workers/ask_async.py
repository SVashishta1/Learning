"""Send questions as background jobs, then poll until every answer is ready.

Usage:  python ask_async.py "Is the wifi free?" "Do you have oat milk?"
        (no questions given = 5 sample questions)
"""
import sys
import time

import httpx

GATEWAY = "http://localhost:8000"
SAMPLES = [
    "Is the wifi free?",
    "Do you have oat milk?",
    "When are you open on Saturday?",
    "Can I bring my dog?",
    "Can I get a refund on beans?",
]

questions = sys.argv[1:] or SAMPLES
start = time.time()

# 1. Submit every question. Each POST returns in a few milliseconds with a job ID (a "ticket").
jobs = {}
for q in questions:
    r = httpx.post(f"{GATEWAY}/jobs", json={"question": q})
    r.raise_for_status()
    job_id = r.json()["job_id"]
    jobs[job_id] = q
    print(f"submitted {job_id}  {q}")
print(f"all {len(jobs)} submitted in {time.time() - start:.2f}s\n")

# 2. Poll: ask about every unfinished job once a second until none are left.
pending = set(jobs)
while pending:
    time.sleep(1)
    for job_id in sorted(pending):
        job = httpx.get(f"{GATEWAY}/jobs/{job_id}").json()
        if job["status"] in ("done", "failed"):
            pending.discard(job_id)
            result = job.get("answer") or job.get("error")
            print(f"[{time.time() - start:5.1f}s] {job_id} {job['status']:6} by {job.get('worker', '?')}: {result}")
    if pending:
        print(f"[{time.time() - start:5.1f}s] still waiting for {len(pending)} job(s)...")

print(f"\nfinished in {time.time() - start:.1f}s")
