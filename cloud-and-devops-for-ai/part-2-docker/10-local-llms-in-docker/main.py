"""Mood API, real-AI edition: a FastAPI app that asks a local open model (run by Ollama).

The word lists from earlier lessons are gone. Now a real language model reads the
text. Ollama runs in its own container; this app talks to it over the compose
network at http://ollama:11434 (set by OLLAMA_URL in compose.yaml).
"""

import os

import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:0.5b")
# Small models on a CPU can take a while, so allow up to 2 minutes per answer.
TIMEOUT_SECONDS = float(os.getenv("OLLAMA_TIMEOUT", "120"))

app = FastAPI(title="Mood API (local LLM)")


class Question(BaseModel):
    question: str = Field(min_length=1, max_length=2000)


class TextIn(BaseModel):
    text: str = Field(min_length=1, max_length=1000)


def ask_ollama(system: str, user: str) -> str:
    """Send one chat message to Ollama and return the model's reply text."""
    try:
        response = httpx.post(
            f"{OLLAMA_URL}/api/chat",
            json={
                "model": OLLAMA_MODEL,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                "stream": False,  # one complete answer instead of word-by-word pieces
                "options": {"temperature": 0},  # 0 = same question, same answer
            },
            timeout=TIMEOUT_SECONDS,
        )
    except httpx.HTTPError as error:
        # 502 = "the server behind me did not answer properly".
        raise HTTPException(502, f"Could not reach Ollama at {OLLAMA_URL}: {error}")
    if response.status_code == 404:
        raise HTTPException(
            503, f"Model '{OLLAMA_MODEL}' is not downloaded yet. Pull it first."
        )
    response.raise_for_status()
    return response.json()["message"]["content"].strip()


@app.get("/health")
def health():
    """Is Ollama up, and is our model downloaded?"""
    try:
        tags = httpx.get(f"{OLLAMA_URL}/api/tags", timeout=5).json()
    except httpx.HTTPError:
        return {"status": "waiting", "ollama": "unreachable", "model": OLLAMA_MODEL}
    names = [m["name"] for m in tags.get("models", [])]
    return {
        "status": "ok" if OLLAMA_MODEL in names else "model-missing",
        "ollama": "ok",
        "model": OLLAMA_MODEL,
        "models_downloaded": names,
    }


@app.post("/ask")
def ask(body: Question):
    answer = ask_ollama("You are a helpful assistant. Answer briefly.", body.question)
    return {"model": OLLAMA_MODEL, "question": body.question, "answer": answer}


@app.post("/predict")
def predict(body: TextIn):
    reply = ask_ollama(
        "Classify the mood of the user's text. "
        "Reply with exactly one word: positive, negative or neutral.",
        body.text,
    )
    # Small models sometimes add a full stop or extra words, so look for the label.
    reply_lower = reply.lower()
    label = next(
        (w for w in ("positive", "negative", "neutral") if w in reply_lower), "unknown"
    )
    return {"model": OLLAMA_MODEL, "text": body.text, "label": label, "raw": reply}
