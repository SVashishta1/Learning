"""llm-service: turns a question + some documents into an answer.

It does ONE job: talk to the AI model. Two modes:
  FAKE_LLM=1 (default)  -> a canned answer built from the documents. Free, no key, works offline.
  FAKE_LLM=0            -> a real answer from Claude (needs ANTHROPIC_API_KEY).
Run alone:  uvicorn main:app --port 8002
"""
import os
import random
import socket
import time

import anthropic
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

FAKE_LLM = os.getenv("FAKE_LLM", "1") == "1"
CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-opus-5-5")  # cheaper option: claude-haiku-5-5
SERVICE_VERSION = os.getenv("SERVICE_VERSION", "1.0")  # lesson 20 builds a 2.0 to practise updates

# "Chaos" knobs to make this service misbehave on purpose (used in lesson 15). Both default to off.
FAIL_RATE = float(os.getenv("FAIL_RATE", "0"))  # 0.3 = 30% of /generate calls fail with error 500
DELAY_SECONDS = float(os.getenv("DELAY_SECONDS", "0"))  # wait this long before answering

SYSTEM_PROMPT = (
    "You answer customer questions for a coffee shop. Use ONLY the numbered documents you are given. "
    "If they do not contain the answer, say you don't know. Answer in at most 3 sentences."
)

app = FastAPI(title="llm-service")
_client = None  # created on first real call, so fake mode never needs a key


def get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        _client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from the environment
    return _client


class GenerateRequest(BaseModel):
    question: str
    context: list[str] = []  # the document texts found by rag-service


def fake_answer(req: GenerateRequest) -> str:
    if not req.context:
        return "(fake LLM) I could not find anything about that in the documents."
    first_sentence = req.context[0].split(". ")[0].rstrip(".")
    return f"(fake LLM) Based on {len(req.context)} document(s): {first_sentence}."


def claude_answer(req: GenerateRequest) -> str:
    docs = "\n".join(f"[{i}] {text}" for i, text in enumerate(req.context, start=1)) or "(no documents found)"
    response = get_client().messages.create(
        model=CLAUDE_MODEL,
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": f"Documents:\n{docs}\n\nQuestion: {req.question}"}],
    )
    if response.stop_reason == "refusal":
        return "Sorry, I can't help with that request."
    # The reply is a list of blocks; keep only the text ones.
    return "".join(block.text for block in response.content if block.type == "text").strip()


@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "llm-service",
        "mode": "fake" if FAKE_LLM else "claude",
        "model": "fake-llm" if FAKE_LLM else CLAUDE_MODEL,
        "version": SERVICE_VERSION,
        "host": socket.gethostname(),
    }


@app.post("/generate")
def generate(req: GenerateRequest):
    if DELAY_SECONDS:
        time.sleep(DELAY_SECONDS)  # pretend the model is slow
    if random.random() < FAIL_RATE:
        raise HTTPException(status_code=500, detail="chaos: simulated LLM failure")
    if FAKE_LLM:
        return {"answer": fake_answer(req), "model": "fake-llm"}
    if not os.getenv("ANTHROPIC_API_KEY"):
        raise HTTPException(status_code=500, detail="FAKE_LLM=0 but ANTHROPIC_API_KEY is not set")
    try:
        return {"answer": claude_answer(req), "model": CLAUDE_MODEL}
    except anthropic.AuthenticationError:
        raise HTTPException(status_code=500, detail="ANTHROPIC_API_KEY is missing or wrong (or set FAKE_LLM=1)")
    except anthropic.APIConnectionError:
        raise HTTPException(status_code=503, detail="could not reach the Claude API")
    except anthropic.APIStatusError as e:
        raise HTTPException(status_code=502, detail=f"Claude API error {e.status_code}")
