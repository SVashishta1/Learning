"""The clinic assistant's brain: local embeddings + local LLM, both served by Ollama on this machine.

Used by ingest.py (build the index) and app.py (answer questions). Nothing here talks to the internet.
"""
import os
import sqlite3
from pathlib import Path

import httpx
import numpy as np

HERE = Path(__file__).parent
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434")
CHAT_MODEL = os.environ.get("CHAT_MODEL", "llama3.2:3b")
EMBED_MODEL = os.environ.get("EMBED_MODEL", "nomic-embed-text")
PROTOCOLS = Path(os.environ.get("PROTOCOLS_DIR", HERE / "protocols"))
DATA = Path(os.environ.get("DATA_DIR", HERE / "data"))
DB = DATA / "clinic.db"
TOP_K = 4                    # how many protocol excerpts the LLM gets
MAX_CHARS = 700              # roughly 170 tokens per chunk: about one section of a protocol

SYSTEM = """You help the staff of a small rural clinic find information in the clinic's own written protocols.
Rules:
- Use ONLY the numbered protocol excerpts you are given. After every fact, cite its number like [1] or [2].
- If the excerpts do not answer the question, say exactly: "The clinic protocols don't cover this. Please ask the clinician in charge."
- Never invent medicine doses, numbers or steps. If a dose is needed, point to the clinic dosing chart.
- If the question mentions any danger sign, start your answer by saying the patient needs urgent referral.
- Answer in short, numbered steps a busy health worker can follow."""

ollama = httpx.Client(base_url=OLLAMA_URL, timeout=180)   # one connection pool, reused for every request


class OllamaError(Exception):
    """A problem talking to the local Ollama server, with a message a person can act on."""


def call_ollama(path, body):
    try:
        response = ollama.post(path, json=body)
    except httpx.ConnectError:
        raise OllamaError(f"Can't reach Ollama at {OLLAMA_URL}. Is it running?") from None
    data = response.json()
    if "error" in data:
        raise OllamaError(f"Ollama says: {data['error']} (did you pull {body.get('model')}?)")
    return data


def installed_models():
    """Names of the models downloaded into Ollama, e.g. ['llama3.2:3b', 'nomic-embed-text:latest']."""
    return [m["name"] for m in ollama.get("/api/tags").json()["models"]]


def has_model(model, names):
    return model in names or f"{model}:latest" in names        # "nomic-embed-text" is stored as "...:latest"


def embed(texts, kind):
    """Turn texts into unit-length vectors. nomic-embed-text wants a prefix saying what the text is for."""
    prefix = "search_document: " if kind == "document" else "search_query: "
    data = call_ollama("/api/embed", {"model": EMBED_MODEL, "input": [prefix + t for t in texts]})
    vectors = np.array(data["embeddings"], dtype=np.float32)
    return vectors / np.linalg.norm(vectors, axis=1, keepdims=True)


def chunk(text):
    """Cut a protocol at its '## ' sections; long sections are split at blank lines.
    Every chunk starts with the protocol title and section name, so it still makes sense on its own."""
    title = text.splitlines()[0].lstrip("# ").strip()
    chunks = []
    for section in text.split("\n## ")[1:]:                 # [0] is the title and disclaimer
        heading, _, body = section.partition("\n")
        current = ""
        for para in [p.strip() for p in body.split("\n\n") if p.strip()]:
            if current and len(current) + len(para) > MAX_CHARS:
                chunks.append((heading, current))
                current = para
            else:
                current = f"{current}\n\n{para}" if current else para
        if current:
            chunks.append((heading, current))
    return [(heading, f"{title}. Section: {heading}.\n{piece}") for heading, piece in chunks]


def build_index():
    """Read every protocol, embed every chunk, and store them in data/clinic.db. Returns the number of chunks."""
    rows = []
    for path in sorted(PROTOCOLS.glob("*.md")):
        for heading, text in chunk(path.read_text(encoding="utf-8")):
            rows.append((path.name, heading, text))
    if not rows:
        raise OllamaError(f"No protocols (*.md) found in {PROTOCOLS}")
    vectors = embed([r[2] for r in rows], kind="document")
    DATA.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DB) as db:
        db.execute("DROP TABLE IF EXISTS chunks")
        db.execute("CREATE TABLE chunks (file TEXT, heading TEXT, text TEXT, vector BLOB)")
        db.executemany("INSERT INTO chunks VALUES (?, ?, ?, ?)",
                       [(f, h, t, v.tobytes()) for (f, h, t), v in zip(rows, vectors)])
    return len(rows)


def load_index():
    if not DB.exists():
        raise OllamaError("No index yet. Run `python ingest.py` first.")
    with sqlite3.connect(DB) as db:
        rows = db.execute("SELECT file, heading, text, vector FROM chunks").fetchall()
    matrix = np.stack([np.frombuffer(r[3], dtype=np.float32) for r in rows])
    return [r[:3] for r in rows], matrix


def search(question, index, k=TOP_K):
    rows, matrix = index
    scores = matrix @ embed([question], kind="query")[0]    # cosine similarity with every chunk
    best = np.argsort(scores)[::-1][:k]
    return [{"file": rows[i][0], "heading": rows[i][1], "text": rows[i][2], "score": round(float(scores[i]), 3)}
            for i in best]


def answer(question, index):
    """Find the best protocol excerpts and let the local LLM answer from them, with citations."""
    hits = search(question, index)
    excerpts = "\n\n".join(f"[{n}] ({h['file']}) {h['text']}" for n, h in enumerate(hits, start=1))
    data = call_ollama("/api/chat", {
        "model": CHAT_MODEL, "stream": False, "options": {"temperature": 0.1},
        "messages": [{"role": "system", "content": SYSTEM},
                     {"role": "user", "content": f"PROTOCOL EXCERPTS:\n{excerpts}\n\nQUESTION: {question}"}]})
    return {"answer": data["message"]["content"].strip(), "sources": hits, "model": CHAT_MODEL}
