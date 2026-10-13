"""Generates a realistic incident: after a 14:02 deploy, checkout-api starts leaking DB connections -> pool exhausted -> 5xx errors."""
import json
import random
from datetime import datetime, timedelta
from pathlib import Path

rng = random.Random(7)
start = datetime(2026, 10, 13, 13, 30)
lines = []
for i in range(0, 60 * 60, 7):
    t = start + timedelta(seconds=i)
    after_deploy = t >= datetime(2026, 10, 13, 14, 2)
    pool_used = min(50, 12 + int(max(0, (t - datetime(2026, 10, 13, 14, 2)).total_seconds()) / 30)) if after_deploy else rng.randint(8, 15)
    svc = rng.choice(["checkout-api", "checkout-api", "search-api", "auth-api"])
    if svc == "checkout-api" and pool_used >= 50 and rng.random() < 0.7:
        lines.append(f"{t:%Y-%m-%dT%H:%M:%S} ERROR checkout-api db: QueuePool limit of size 50 overflow 0 reached, connection timed out after 30s")
        lines.append(f"{t:%Y-%m-%dT%H:%M:%S} ERROR checkout-api POST /api/checkout 503 30012ms")
    elif svc == "checkout-api" and after_deploy and rng.random() < 0.2:
        lines.append(f"{t:%Y-%m-%dT%H:%M:%S} WARN checkout-api db pool usage {pool_used}/50 (connections not returned: payment_retry handler)")
    else:
        lines.append(f"{t:%Y-%m-%dT%H:%M:%S} INFO {svc} GET /health 200 {rng.randint(2, 40)}ms")
    if rng.random() < 0.02:
        lines.append(f"{t:%Y-%m-%dT%H:%M:%S} WARN search-api slow query 1200ms (index rebuild scheduled)")

Path("incident_data").mkdir(exist_ok=True)
Path("incident_data/app.log").write_text("\n".join(lines) + "\n")
metrics = {"window": "13:30-14:30 UTC", "checkout-api": {"error_rate_pct": {"13:45": 0.2, "14:00": 0.3, "14:15": 18.5, "14:30": 41.0},
           "p95_latency_ms": {"13:45": 180, "14:00": 190, "14:15": 9800, "14:30": 30000},
           "db_pool_in_use": {"13:45": 11, "14:00": 12, "14:15": 47, "14:30": 50}},
           "search-api": {"error_rate_pct": {"14:30": 0.4}, "p95_latency_ms": {"14:30": 420}},
           "auth-api": {"error_rate_pct": {"14:30": 0.1}, "p95_latency_ms": {"14:30": 95}}}
Path("incident_data/metrics.json").write_text(json.dumps(metrics, indent=2))
deploys = [{"time": "2026-10-13T11:20", "service": "search-api", "version": "v3.8.0", "change": "Upgrade search index library"},
           {"time": "2026-10-13T14:02", "service": "checkout-api", "version": "v2.14.0", "change": "Add automatic payment retries (payment_retry handler)"}]
Path("incident_data/deploys.json").write_text(json.dumps(deploys, indent=2))
print(f"Wrote incident_data/ ({len(lines)} log lines, metrics, deploys)")
