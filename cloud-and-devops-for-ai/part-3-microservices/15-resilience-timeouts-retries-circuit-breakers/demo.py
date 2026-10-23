"""Poke the gateway and print what happens. Use it while you break things on purpose.

  python demo.py ask 10     send 10 questions, one after another, and show each result
  python demo.py health     show the gateway's circuit breakers
  python demo.py idem       send the SAME job twice with one Idempotency-Key, then once without
"""
import sys
import time
import uuid

import httpx

GATEWAY = "http://localhost:8000"


def ask(n: int) -> None:
    for i in range(1, n + 1):
        start = time.perf_counter()
        try:
            r = httpx.post(f"{GATEWAY}/ask", json={"question": "Is the wifi free?"}, timeout=60)
            took = time.perf_counter() - start
            body = r.json()
            if r.status_code == 200:
                kind = "DEGRADED" if body["degraded"] else "ok"
                print(f"{i:2}. {r.status_code} {kind:8} {took:5.2f}s  {body['answer'][:70]}")
            else:
                print(f"{i:2}. {r.status_code} error    {took:5.2f}s  {body['detail'][:70]}")
        except httpx.HTTPError as e:
            print(f"{i:2}. no answer from the gateway: {e.__class__.__name__}")
        time.sleep(0.3)
    health()


def health() -> None:
    breakers = httpx.get(f"{GATEWAY}/health").json()["breakers"]
    for name, b in breakers.items():
        print(f"    breaker {name:12} state={b['state']:9} failures_in_a_row={b['failures_in_a_row']}")


def idem() -> None:
    key = uuid.uuid4().hex  # in a real client: make one key per user action, reuse it on every retry
    for label, headers in [("1st send, key", {"Idempotency-Key": key}),
                           ("2nd send, same key", {"Idempotency-Key": key}),
                           ("3rd send, no key", {})]:
        r = httpx.post(f"{GATEWAY}/jobs", json={"question": "Do you have oat milk?"}, headers=headers)
        replay = r.headers.get("Idempotent-Replay", "-")
        print(f"{label:20} -> {r.status_code}  job_id={r.json()['job_id']}  Idempotent-Replay={replay}")


if __name__ == "__main__":
    command = sys.argv[1] if len(sys.argv) > 1 else "ask"
    if command == "ask":
        ask(int(sys.argv[2]) if len(sys.argv) > 2 else 5)
    elif command == "health":
        health()
    elif command == "idem":
        idem()
    else:
        print(__doc__)
