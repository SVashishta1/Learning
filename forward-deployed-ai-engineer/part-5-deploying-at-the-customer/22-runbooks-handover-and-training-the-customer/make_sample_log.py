"""make_sample_log.py: creates 30 days of request logs for the Northwind reply assistant (fictional, seeded).

    python make_sample_log.py            -> requests.jsonl (about 28,000 lines, ~2.4 MB)

One JSON object per line: {"ts": "...", "status": 200, "latency_ms": 2140, "route": "/draft"}.
Two things go wrong on purpose: day 18 has a 2-hour model-provider outage (503s),
and on day 25 a slow prompt change makes answers slow for 6 hours.
"""
import json
import random
from datetime import datetime, timedelta
from pathlib import Path

START = datetime(2026, 9, 1)
OUT = Path(__file__).parent / "requests.jsonl"


def main(path: Path = OUT, days: int = 30, seed: int = 7) -> int:
    rnd = random.Random(seed)
    n = 0
    with path.open("w", encoding="utf-8") as f:
        for minute in range(days * 24 * 60):
            ts = START + timedelta(minutes=minute)
            busy = 9 <= ts.hour < 18 and ts.weekday() < 5              # office hours, Monday-Friday
            for _ in range(rnd.choices([0, 1, 2, 3], weights=[1, 3, 3, 2] if busy else [12, 2, 1, 0])[0]):
                latency = rnd.lognormvariate(7.6, 0.45)                # typical answer ~2 s, a few slower
                status = 200 if rnd.random() > 0.002 else rnd.choice([500, 502])
                if ts.day == 18 and 10 <= ts.hour < 12:                # the model provider outage
                    status, latency = (503, 30000) if rnd.random() < 0.7 else (200, latency)
                if ts.day == 25 and 13 <= ts.hour < 19:                # the slow prompt change
                    latency *= 3.5
                f.write(json.dumps({"ts": ts.isoformat(), "status": status, "latency_ms": int(latency),
                                    "route": "/draft"}) + "\n")
                n += 1
    return n


if __name__ == "__main__":
    print(f"Wrote {main()} requests to {OUT.name}")
