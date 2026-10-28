"""slo_report.py: turn raw request logs into the SLO numbers you hand over to the customer.

    python slo_report.py requests.jsonl
    python slo_report.py requests.jsonl --availability 99.5 --latency-ms 8000 --latency-target 95

SLI  (indicator) = what we measure        e.g. share of requests that did not fail with a 5xx
SLO  (objective) = the target for an SLI  e.g. 99.5 % over 30 days
Error budget     = what the SLO allows to fail: 0.5 % of requests. Spend it on releases, not on surprises.
Burn rate        = how fast the budget is being spent. 1.0 = exactly on budget; 14.4 = the 30-day budget gone in ~2 days.
"""
import argparse
import json
import math
from collections import defaultdict
from datetime import datetime, timedelta


def load(path: str) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def percentile(values: list[int], p: float) -> float:
    s = sorted(values)
    return s[min(len(s) - 1, math.ceil(p / 100 * len(s)) - 1)] if s else 0.0


def report(rows: list[dict], availability_slo=99.5, latency_ms=8000, latency_slo=95.0) -> dict:
    total = len(rows)
    bad = sum(r["status"] >= 500 for r in rows)                      # 4xx are the caller's mistake, not ours
    slow = sum(r["latency_ms"] > latency_ms for r in rows)
    allowed_bad = total * (1 - availability_slo / 100)
    by_day, by_hour = defaultdict(lambda: [0, 0, 0]), defaultdict(lambda: [0, 0])
    for r in rows:
        ts = datetime.fromisoformat(r["ts"])
        d = by_day[ts.date().isoformat()]
        d[0] += 1
        d[1] += r["status"] >= 500
        d[2] += r["latency_ms"] > latency_ms
        h = by_hour[ts.replace(minute=0, second=0).isoformat()]
        h[0] += 1
        h[1] += r["status"] >= 500
    # Burn-rate alert (idea from the Google SRE workbook): page when an hour burns budget more than 14.4x
    # faster than allowed. Ignore quiet hours (< 20 requests): 1 error out of 3 requests at night is not a fire.
    budget_rate = 1 - availability_slo / 100
    pages = []
    for hour in sorted(by_hour):
        n, b = by_hour[hour]
        if n >= 20 and (b / n) / budget_rate > 14.4:
            pages.append(f"{hour[:13]}:00 burn rate {(b / n) / budget_rate:.0f}x")
    return {
        "requests": total, "days": len(by_day),
        "availability": 100 * (1 - bad / total),
        "availability_slo": availability_slo,
        "error_budget_requests": allowed_bad,
        "budget_used_pct": 100 * bad / allowed_bad if allowed_bad else 0.0,
        "latency_p50_ms": percentile([r["latency_ms"] for r in rows], 50),
        "latency_p95_ms": percentile([r["latency_ms"] for r in rows], 95),
        "fast_enough_pct": 100 * (1 - slow / total),
        "latency_slo": latency_slo, "latency_ms": latency_ms,
        "worst_days": sorted(((d, v[1], v[2], v[0]) for d, v in by_day.items()), key=lambda x: -(x[1] + x[2]))[:3],
        "pages": pages,
    }


def show(r: dict) -> str:
    ok = lambda good: "MET   " if good else "MISSED"                     # noqa: E731
    lines = [
        f"Requests: {r['requests']:,} over {r['days']} days",
        f"[{ok(r['availability'] >= r['availability_slo'])}] Availability {r['availability']:.3f} %  (SLO {r['availability_slo']} %)",
        f"         Error budget: {r['error_budget_requests']:.0f} failed requests allowed, {r['budget_used_pct']:.0f} % used",
        f"[{ok(r['fast_enough_pct'] >= r['latency_slo'])}] Under {r['latency_ms'] / 1000:.0f} s: {r['fast_enough_pct']:.2f} %  "
        f"(SLO {r['latency_slo']} %)  p50 {r['latency_p50_ms'] / 1000:.1f} s, p95 {r['latency_p95_ms'] / 1000:.1f} s",
        "Worst days (date, 5xx, slow, requests):",
        *[f"   {d}  {b:>5} {s:>5} {n:>6}" for d, b, s, n in r["worst_days"]],
        f"Hours that would have paged on-call ({len(r['pages'])}):",
        *[f"   {p}" for p in r["pages"]],
    ]
    return "\n".join(lines)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="SLO report from JSON-lines request logs")
    ap.add_argument("log")
    ap.add_argument("--availability", type=float, default=99.5)
    ap.add_argument("--latency-ms", type=int, default=8000)
    ap.add_argument("--latency-target", type=float, default=95.0)
    a = ap.parse_args()
    print(show(report(load(a.log), a.availability, a.latency_ms, a.latency_target)))
