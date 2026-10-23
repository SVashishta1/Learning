"""Mood API, team edition: the API + a database (Postgres) + a cache (Redis).

- Redis remembers recent answers, so asking the same thing twice is instant.
- Postgres keeps a history of every prediction, even after a restart.
Both addresses come from environment variables that compose.yaml sets.
"""

import json
import os
from contextlib import asynccontextmanager

import psycopg
import redis
from fastapi import FastAPI
from pydantic import BaseModel, Field

# "db" and "cache" are the service names in compose.yaml. Inside the compose
# network, each service name works like a web address.
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://mood:mood@localhost:5432/mood")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
CACHE_SECONDS = 3600  # forget cached answers after 1 hour

cache = redis.Redis.from_url(REDIS_URL, decode_responses=True)

POSITIVE_WORDS = {"good", "great", "love", "happy", "excellent", "amazing", "nice"}
NEGATIVE_WORDS = {"bad", "terrible", "hate", "sad", "awful", "horrible", "broken"}


def predict_mood(text: str) -> dict:
    words = [word.strip(".,!?;:\"'()").lower() for word in text.split()]
    score = sum(w in POSITIVE_WORDS for w in words) - sum(
        w in NEGATIVE_WORDS for w in words
    )
    label = "positive" if score > 0 else "negative" if score < 0 else "neutral"
    return {"label": label, "score": score}


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Runs once when the API starts: make sure the history table exists.
    with psycopg.connect(DATABASE_URL) as conn:
        conn.execute(
            """CREATE TABLE IF NOT EXISTS predictions (
                   id SERIAL PRIMARY KEY,
                   text TEXT NOT NULL,
                   label TEXT NOT NULL,
                   created_at TIMESTAMPTZ NOT NULL DEFAULT now()
               )"""
        )
    yield  # the app runs while we wait here


app = FastAPI(title="Mood API (compose)", lifespan=lifespan)


class TextIn(BaseModel):
    text: str = Field(min_length=1, max_length=1000)


@app.get("/health")
def health():
    # Healthy only if BOTH helpers answer.
    with psycopg.connect(DATABASE_URL) as conn:
        conn.execute("SELECT 1")
    cache.ping()
    return {"status": "ok", "database": "ok", "cache": "ok"}


@app.post("/predict")
def predict(body: TextIn):
    key = "mood:" + body.text.lower()
    saved = cache.get(key)
    if saved:
        result = json.loads(saved)
        result["cached"] = True
    else:
        result = predict_mood(body.text)
        # ex= sets an expiry time in seconds.
        cache.set(key, json.dumps(result), ex=CACHE_SECONDS)
        result["cached"] = False

    # "with" opens a connection and commits (saves) when the block ends.
    # %s placeholders keep user text safely separate from the SQL.
    with psycopg.connect(DATABASE_URL) as conn:
        conn.execute(
            "INSERT INTO predictions (text, label) VALUES (%s, %s)",
            (body.text, result["label"]),
        )
    return {"text": body.text, **result}


@app.get("/history")
def history(limit: int = 10):
    with psycopg.connect(DATABASE_URL) as conn:
        rows = conn.execute(
            "SELECT id, text, label, created_at FROM predictions "
            "ORDER BY id DESC LIMIT %s",
            (limit,),
        ).fetchall()
    return [
        {"id": r[0], "text": r[1], "label": r[2], "created_at": r[3].isoformat()}
        for r in rows
    ]
