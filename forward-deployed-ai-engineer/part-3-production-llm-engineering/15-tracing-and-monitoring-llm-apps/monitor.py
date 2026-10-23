"""monitor.py: read the spans in traces.jsonl, compute health numbers, and raise alerts from alert_rules.json.

python monitor.py                 # all spans in the file
python monitor.py --minutes 15    # only the last 15 minutes (what you'd run every few minutes from cron)
Set ALERT_WEBHOOK_URL (e.g. a Slack or Teams incoming-webhook URL) to also send firing alerts there.
Exit code: 0 = healthy, 2 = at least one alert is firing (so a scheduler or CI step can react).
"""
import argparse
import json
import os
import sys
import time
from pathlib import Path

import telemetry

RULES_FILE = Path(__file__).with_name("alert_rules.json")


def load_spans(minutes: float | None = None) -> list[dict]:
    if not telemetry.TRACE_FILE.exists():
        return []
    spans = [json.loads(line) for line in telemetry.TRACE_FILE.open(encoding="utf-8") if line.strip()]
    if minutes:
        since = time.time() - minutes * 60
        spans = [s for s in spans if s["start"] >= since]
    return spans


def health(spans: list[dict]) -> dict:
    roots = [s for s in spans if s["name"] == "handle_question"]
    chats = [s for s in spans if s["name"].startswith("chat ")]
    retrievals = [s for s in spans if s["name"] == "retrieve"]
    if not roots:
        return {"requests": 0}
    latencies = sorted(s["duration_ms"] for s in roots)
    answered = [s for s in roots if "app.answer.idk" in s["attributes"]]
    cost = sum(s["attributes"].get("app.cost_usd", 0) for s in chats)
    return {
        "requests": len(roots),
        "error_rate": sum(s["status"] == "ERROR" for s in roots) / len(roots),
        "p50_latency_ms": latencies[len(latencies) // 2],
        "p95_latency_ms": latencies[min(len(latencies) - 1, round(0.95 * len(latencies)) - 1)],
        "idk_rate": sum(s["attributes"]["app.answer.idk"] for s in answered) / max(len(answered), 1),
        "empty_retrieval_rate": sum(s["attributes"].get("retrieval.best_score", 0) == 0 for s in retrievals) / max(len(retrievals), 1),
        "tool_errors": sum("tool error" in s["events"] for s in roots),
        "cost_per_1000_requests_usd": cost / len(roots) * 1000,
        "tokens_per_request": sum(s["attributes"].get("gen_ai.usage.input_tokens", 0)
                                  + s["attributes"].get("gen_ai.usage.output_tokens", 0) for s in chats) / len(roots),
    }


def check(stats: dict, rules: list[dict]) -> list[str]:
    if stats.get("requests", 0) < 10:
        return []                                    # too little traffic to judge: avoid noisy alerts
    firing = []
    for rule in rules:
        value = stats.get(rule["metric"])
        if value is not None and ((rule["op"] == ">" and value > rule["threshold"]) or
                                  (rule["op"] == "<" and value < rule["threshold"])):
            firing.append(f"[{rule['severity'].upper()}] {rule['metric']} = {round(value, 3):,} "
                          f"(limit {rule['op']} {rule['threshold']}): {rule['action']}")
    return firing


def notify(alerts: list[str]):
    url = os.getenv("ALERT_WEBHOOK_URL")
    if url and alerts:
        import httpx
        httpx.post(url, json={"text": "Northwind assistant alerts:\n" + "\n".join(alerts)}, timeout=10)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--minutes", type=float, help="only look at the last N minutes")
    args = p.parse_args()
    stats = health(load_spans(args.minutes))
    if not stats["requests"]:
        print("No requests found in traces.jsonl. Run: python app.py --simulate 60 --offline --exporter file")
        return
    print("Health of northwind-assistant" + (f" (last {args.minutes:g} min)" if args.minutes else ""))
    for name, value in stats.items():
        print(f"  {name:28s} {value:,.3f}" if isinstance(value, float) else f"  {name:28s} {value}")
    alerts = check(stats, json.loads(RULES_FILE.read_text()))
    print("\n" + ("\n".join(alerts) if alerts else "✅ All alert rules OK"))
    notify(alerts)
    sys.exit(2 if alerts else 0)


if __name__ == "__main__":
    main()
