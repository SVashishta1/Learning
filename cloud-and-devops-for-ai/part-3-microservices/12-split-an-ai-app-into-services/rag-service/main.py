"""rag-service: finds the documents that best match a question.

It does ONE job: search. It never talks to an AI model.
Run alone:  uvicorn main:app --port 8001
"""
import json
import os
import re
import socket

from fastapi import FastAPI
from pydantic import BaseModel

# Which file holds the documents. Lesson 19 swaps it for a file from a Kubernetes ConfigMap.
DOCS_FILE = os.getenv("DOCS_FILE", os.path.join(os.path.dirname(__file__), "docs.json"))

# Little words that appear everywhere and tell us nothing about the topic.
STOP_WORDS = {
    "a", "an", "and", "are", "can", "do", "does", "for", "how", "i", "if", "in", "is",
    "it", "my", "of", "on", "or", "the", "to", "we", "what", "when", "where", "you", "your",
}


def load_docs(path: str) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def words(text: str) -> set[str]:
    """'Are dogs allowed on the Wi-Fi?' -> {'dog', 'allowed', 'wifi'}"""
    found = set()
    for w in re.findall(r"[a-z0-9]+", text.lower().replace("-", "")):
        if w in STOP_WORDS:
            continue
        if len(w) > 3 and w.endswith("s"):
            w = w[:-1]  # tiny "stemming": dogs -> dog, hours -> hour
        found.add(w)
    return found


DOCS = load_docs(DOCS_FILE)
app = FastAPI(title="rag-service")


class SearchRequest(BaseModel):
    question: str
    top_k: int = 2  # how many documents to send back at most


@app.get("/health")
def health():
    return {"status": "ok", "service": "rag-service", "documents": len(DOCS), "host": socket.gethostname()}


@app.post("/search")
def search(req: SearchRequest):
    question_words = words(req.question)
    scored = []
    for doc in DOCS:
        # Score = how many question words also appear in the document. Simple keyword search;
        # real RAG uses embeddings (ai-from-zero lessons 21-24), but the service boundary is the same.
        score = len(question_words & words(doc["title"] + " " + doc["text"]))
        if score > 0:
            scored.append({**doc, "score": score})
    scored.sort(key=lambda d: d["score"], reverse=True)
    return {"results": scored[: req.top_k]}
