"""safe_log.py: log what you need to debug, without leaking customer data or secrets.

Default: NO prompt text, only a fingerprint (hash) and the length. Set LOG_CONTENT=1 to also log text,
which is then redacted (emails, phone numbers, UK postcodes, card numbers, API keys) and shortened.
"""
import hashlib
import json
import logging
import os
import re
import sys

LOG_CONTENT = os.getenv("LOG_CONTENT", "0") == "1"
MAX_CHARS = 300
PATTERNS = [   # (what, regular expression) -- the same idea as lesson 09, kept small here
    ("API_KEY", r"sk-ant-[\w-]{10,}"),
    ("EMAIL", r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+"),
    ("CARD", r"\b(?:\d[ -]?){13,16}\b"),
    ("PHONE", r"(?:\+44\s?|\b0)(?:\d\s?){9,10}\b"),
    ("POSTCODE", r"\b[A-Z]{1,2}\d[A-Z\d]?\s?\d[A-Z]{2}\b"),
]


def redact(text: str) -> str:
    for label, pattern in PATTERNS:
        text = re.sub(pattern, f"[{label}]", text)
    return text


def fingerprint(text: str) -> str:
    """Same text -> same 12 characters. Lets you find repeats and join logs to traces without storing the text."""
    return hashlib.sha256(text.encode()).hexdigest()[:12]


def content_fields(name: str, text: str) -> dict:
    fields = {f"{name}.sha": fingerprint(text), f"{name}.chars": len(text)}
    if LOG_CONTENT:
        safe = redact(text)
        fields[name] = safe[:MAX_CHARS] + ("…" if len(safe) > MAX_CHARS else "")
    return fields


class JsonFormatter(logging.Formatter):
    """One JSON object per line: easy for log tools (Loki, CloudWatch, Datadog...) to search and count."""
    def format(self, record):
        entry = {"time": self.formatTime(record, "%Y-%m-%dT%H:%M:%S"), "level": record.levelname, "event": record.getMessage()}
        entry.update(getattr(record, "fields", {}))
        return json.dumps(entry, ensure_ascii=False)


def get_logger(name: str = "northwind") -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stderr)
        handler.setFormatter(JsonFormatter())
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger


def log(event: str, level: int = logging.INFO, **fields):
    get_logger().log(level, event, extra={"fields": fields})
