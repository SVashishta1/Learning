"""cost_tools.py: the money-and-speed toolkit.

  token math        estimate_tokens(), count_tokens(), monthly_cost()
  prompt caching    llm.chat(..., cache=True) marks the big, unchanging system prompt (see answer())
  response caching  ResponseCache: the same question twice -> answer from SQLite, $0, milliseconds
  model routing     route(): easy questions to the cheap model, hard ones to the strong model
  batching          batch_requests(): many jobs in one Message Batches request, half price, done within 24 h
"""
import hashlib
import json
import re
import sqlite3
import time
from pathlib import Path
from typing import Literal

from pydantic import BaseModel

import llm

HANDBOOK = Path(__file__).with_name("policy_handbook.md").read_text(encoding="utf-8")
SYSTEM = ("You answer Northwind Logistics customers in at most 3 sentences, using only this handbook. "
          "If it doesn't say, answer \"I don't know, please contact support.\"\n\n<handbook>\n" + HANDBOOK + "\n</handbook>")
BATCH_DISCOUNT = 0.5           # Message Batches cost 50% of the normal price


# ---------------- 1. Token math ----------------
def estimate_tokens(text: str) -> int:
    """Rough rule for English: 1 token is about 4 characters (about 3/4 of a word). Good for planning."""
    return max(1, round(len(text) / 4))


def count_tokens(system: str, question: str, model: str | None = None) -> int:
    """Exact count from the API (free to call, needs a key). Use it before you commit to a design."""
    result = llm.claude_client().messages.count_tokens(model=model or llm.MODEL, system=system,
                                                       messages=[{"role": "user", "content": question}])
    return result.input_tokens


def monthly_cost(requests_per_day: int, input_tokens: int, output_tokens: int, model: str,
                 cached_tokens: int = 0, cache_hit_rate: float = 0.0, response_cache_hit_rate: float = 0.0,
                 batch: bool = False) -> float:
    """What a feature costs per 30-day month. cached_tokens = the part of the input that can be cached."""
    calls = requests_per_day * 30 * (1 - response_cache_hit_rate)           # response-cache hits cost nothing
    hits = calls * cache_hit_rate
    misses = calls - hits
    per_hit = llm.cost_usd(model, input_tokens - cached_tokens, output_tokens, cache_read=cached_tokens)
    per_miss = llm.cost_usd(model, input_tokens - cached_tokens, output_tokens, cache_write=cached_tokens) \
        if cached_tokens else llm.cost_usd(model, input_tokens, output_tokens)
    return (hits * per_hit + misses * per_miss) * (BATCH_DISCOUNT if batch else 1)


# ---------------- 2. Answer, with or without prompt caching ----------------
def answer(question: str, model: str | None = None, cache: bool = True) -> llm.Reply:
    """The system prompt (handbook) is identical every time, so it can be cached; only the question changes."""
    return llm.chat(question, system=SYSTEM, model=model, cache=cache, effort="low", max_tokens=400)


# ---------------- 3. Response cache ----------------
def normalise(text: str) -> str:
    """'  What's the Express CUT-OFF?? ' and 'whats the express cut-off' become the same key."""
    return re.sub(r"\s+", " ", re.sub(r"[^\w\s£:-]", "", text.lower())).strip()


class ResponseCache:
    """Exact-match cache in SQLite. The key includes the model and a hash of the system prompt, so changing
    either one automatically ignores old answers. ttl_seconds stops answers living forever."""
    def __init__(self, path: str = "response_cache.db", ttl_seconds: int = 24 * 3600):
        self.db = sqlite3.connect(path)
        self.ttl = ttl_seconds
        self.db.execute("CREATE TABLE IF NOT EXISTS cache (key TEXT PRIMARY KEY, answer TEXT, created REAL)")

    def key(self, model: str, system: str, question: str) -> str:
        return hashlib.sha256(f"{model}\n{hashlib.sha256(system.encode()).hexdigest()}\n{normalise(question)}".encode()).hexdigest()

    def get(self, model: str, system: str, question: str) -> str | None:
        row = self.db.execute("SELECT answer, created FROM cache WHERE key = ?",
                              (self.key(model, system, question),)).fetchone()
        return row[0] if row and time.time() - row[1] < self.ttl else None

    def put(self, model: str, system: str, question: str, answer: str):
        self.db.execute("INSERT OR REPLACE INTO cache VALUES (?, ?, ?)",
                        (self.key(model, system, question), answer, time.time()))
        self.db.commit()


# ---------------- 4. Model routing ----------------
class Difficulty(BaseModel):
    level: Literal["easy", "hard"]


ROUTER_SYSTEM = ("Classify a customer question for Northwind Logistics. easy = a single fact lookup (a price, a time, "
                 "a form name, yes/no). hard = needs reasoning, combining several rules, a complaint or an exception.")


def route(question: str) -> tuple[str, llm.Reply]:
    """Ask the CHEAP model how hard the question is (costs a fraction of a cent), then pick the answering model."""
    reply = llm.chat(question, system=ROUTER_SYSTEM, model=llm.CHEAP_MODEL, schema=Difficulty, effort="low",
                     max_tokens=100)
    return (llm.CHEAP_MODEL if reply.parsed.level == "easy" else llm.MODEL), reply


# ---------------- 5. Batching ----------------
def batch_requests(tickets: list[dict], model: str | None = None) -> list[dict]:
    """One Message Batches request per ticket. custom_id lets you match results back (they arrive in any order)."""
    return [{"custom_id": t["id"],
             "params": {"model": model or llm.CHEAP_MODEL, "max_tokens": 300, "output_config": {"effort": "low"},
                        "system": "Summarise this Northwind support ticket in one sentence and suggest the next action.",
                        "messages": [{"role": "user", "content": t["text"]}]}}
            for t in tickets]


def save_jsonl(rows: list[dict], path: str):
    Path(path).write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")


if __name__ == "__main__":
    # A planning calculator: what would the handbook Q&A cost per month at 5,000 questions a day?
    import sys
    system_tokens = estimate_tokens(SYSTEM)
    question_tokens, answer_tokens = 20, 80
    print(f"Handbook system prompt ≈ {system_tokens} tokens (estimate: characters / 4)")
    if "--exact" in sys.argv:
        print(f"Exact count from the API: {count_tokens(SYSTEM, 'How much is Saturday delivery?')} tokens (incl. question)")
    total_in = system_tokens + question_tokens
    print(f"Each request ≈ {total_in} input + {answer_tokens} output tokens; 5,000 requests/day for 30 days\n")
    plans = [("Opus, no caching", dict(model="claude-opus-5-5")),
             ("Opus, 90% prompt-cache hits", dict(model="claude-opus-5-5", cached_tokens=system_tokens, cache_hit_rate=0.9)),
             ("  + 25% response-cache hits", dict(model="claude-opus-5-5", cached_tokens=system_tokens, cache_hit_rate=0.9,
                                                  response_cache_hit_rate=0.25)),
             ("Haiku, 90% prompt-cache hits", dict(model="claude-haiku-5-5", cached_tokens=system_tokens, cache_hit_rate=0.9)),
             ("Opus as a nightly batch", dict(model="claude-opus-5-5", batch=True))]
    for name, kwargs in plans:
        print(f"{name:30s} ${monthly_cost(5000, total_in, answer_tokens, **kwargs):>9,.2f} / month")
