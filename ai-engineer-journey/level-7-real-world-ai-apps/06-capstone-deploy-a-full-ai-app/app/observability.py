"""Logging + metrics: how you know what your AI app is doing in production."""
import json
import logging
import sys
import time

from prometheus_client import Counter, Histogram

REQUESTS = Counter("ai_requests_total", "Requests by endpoint and status", ["endpoint", "status"])
LATENCY = Histogram("ai_request_seconds", "Request latency", ["endpoint"], buckets=(0.1, 0.5, 1, 2, 5, 10, 30))
TOKENS = Counter("ai_tokens_total", "LLM tokens used", ["direction"])
COST = Counter("ai_cost_usd_total", "Estimated LLM spend in USD")
PRICES = {"claude-opus-5-5": (4.0, 20.0), "claude-sonnet-5-5": (2.0, 10.0), "claude-haiku-5-5": (0.10, 0.50)}


class JsonFormatter(logging.Formatter):
    """One JSON object per line: easy to search in any log tool (CloudWatch, Datadog, Grafana Loki...)."""
    def format(self, record):
        base = {"ts": round(time.time(), 3), "level": record.levelname, "msg": record.getMessage()}
        return json.dumps({**base, **getattr(record, "extra_fields", {})})


def get_logger():
    log = logging.getLogger("ai-app")
    if not log.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(JsonFormatter())
        log.addHandler(handler)
        log.setLevel(logging.INFO)
    return log


def record_usage(model: str, input_tokens: int, output_tokens: int) -> float:
    TOKENS.labels("input").inc(input_tokens)
    TOKENS.labels("output").inc(output_tokens)
    p_in, p_out = PRICES.get(model, (0, 0))
    cost = (input_tokens * p_in + output_tokens * p_out) / 1e6
    COST.inc(cost)
    return cost
