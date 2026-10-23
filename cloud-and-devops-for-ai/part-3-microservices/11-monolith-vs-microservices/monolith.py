"""The whole AI app in ONE program: a "monolith".

Three jobs live side by side in this file:
  1. search_docs()     - find documents that match the question  (lesson 12 turns this into rag-service)
  2. generate_answer() - ask the AI model, or fake it             (lesson 12 turns this into llm-service)
  3. ask()             - the web address users call              (lesson 12 turns this into gateway)

Run:  uvicorn monolith:app --port 8000
"""
import os
import re
import time

import anthropic
from fastapi import FastAPI
from pydantic import BaseModel

FAKE_LLM = os.getenv("FAKE_LLM", "1") == "1"  # 1 = free canned answers, 0 = real Claude
CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-opus-5-5")

DOCS = [
    {"title": "Opening hours", "text": "Moonbeam Coffee is open from 7am to 7pm on weekdays and from 8am to 5pm on weekends."},
    {"title": "Wi-Fi", "text": "Free Wi-Fi is available in every shop. The network name is MoonbeamGuest."},
    {"title": "Milk options", "text": "We offer whole milk, oat milk, almond milk and soy milk. Plant-based milk costs no extra."},
    {"title": "Pets", "text": "Dogs are welcome on the terrace and inside our Riverside shop."},
]
STOP_WORDS = {"a", "an", "and", "are", "can", "do", "i", "is", "it", "my", "of", "on", "the", "to", "you", "your"}

app = FastAPI(title="monolith")


class AskRequest(BaseModel):
    question: str


# ---------- Job 1: search ----------
def words(text: str) -> set[str]:
    found = set()
    for w in re.findall(r"[a-z0-9]+", text.lower().replace("-", "")):
        if w not in STOP_WORDS:
            found.add(w[:-1] if len(w) > 3 and w.endswith("s") else w)
    return found


def search_docs(question: str, top_k: int = 2) -> list[dict]:
    q = words(question)
    scored = [(len(q & words(d["title"] + " " + d["text"])), d) for d in DOCS]
    return [d for score, d in sorted(scored, key=lambda x: x[0], reverse=True) if score > 0][:top_k]


# ---------- Job 2: the AI model ----------
def generate_answer(question: str, context: list[str]) -> str:
    if FAKE_LLM:
        if not context:
            return "(fake LLM) I could not find anything about that in the documents."
        return f"(fake LLM) Based on {len(context)} document(s): {context[0]}"
    docs = "\n".join(f"[{i}] {t}" for i, t in enumerate(context, start=1)) or "(no documents found)"
    response = anthropic.Anthropic().messages.create(
        model=CLAUDE_MODEL,
        max_tokens=1024,
        system="Answer using ONLY the numbered documents. If they don't say, say you don't know. Max 3 sentences.",
        messages=[{"role": "user", "content": f"Documents:\n{docs}\n\nQuestion: {question}"}],
    )
    return "".join(block.text for block in response.content if block.type == "text").strip()


# ---------- Job 3: the web address ----------
@app.get("/health")
def health():
    return {"status": "ok", "service": "monolith"}


@app.post("/ask")
def ask(req: AskRequest):
    t0 = time.perf_counter()
    found = search_docs(req.question)  # a normal function call: fast, can't get lost on a network
    answer = generate_answer(req.question, [d["text"] for d in found])
    return {
        "question": req.question,
        "answer": answer,
        "sources": [d["title"] for d in found],
        "took_ms": round((time.perf_counter() - t0) * 1000),
    }
