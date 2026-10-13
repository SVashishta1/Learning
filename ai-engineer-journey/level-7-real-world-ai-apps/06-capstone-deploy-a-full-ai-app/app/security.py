"""API-key auth + per-key rate limiting + a daily spending cap. Without these, one leaked URL can drain your credit card."""
import os
import time
from collections import defaultdict, deque

from fastapi import Header, HTTPException

API_KEYS = {k.strip() for k in os.getenv("APP_API_KEYS", "dev-key-123").split(",") if k.strip()}
RATE_LIMIT = int(os.getenv("RATE_LIMIT_PER_MINUTE", "20"))
DAILY_BUDGET_USD = float(os.getenv("DAILY_BUDGET_USD", "2.0"))

_calls: dict[str, deque] = defaultdict(deque)
_spend = {"day": time.strftime("%Y-%m-%d"), "usd": 0.0}


def require_api_key(x_api_key: str = Header(default="")) -> str:
    if x_api_key not in API_KEYS:
        raise HTTPException(401, "Missing or invalid X-API-Key header")
    window = _calls[x_api_key]
    now = time.monotonic()
    while window and now - window[0] > 60:          # sliding 60-second window
        window.popleft()
    if len(window) >= RATE_LIMIT:
        raise HTTPException(429, f"Rate limit: {RATE_LIMIT} requests per minute", headers={"Retry-After": "60"})
    window.append(now)
    return x_api_key


def check_budget():
    today = time.strftime("%Y-%m-%d")
    if _spend["day"] != today:
        _spend.update(day=today, usd=0.0)
    if _spend["usd"] >= DAILY_BUDGET_USD:
        raise HTTPException(503, "Daily AI budget reached. Try again tomorrow.")


def add_spend(usd: float):
    _spend["usd"] += usd
