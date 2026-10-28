"""assistant.py: a warehouse-procedures assistant that runs with NO internet at all.

    Local embeddings  (POST {MODEL_URL}/embeddings,        e.g. nomic-embed-text in Ollama, or a vLLM embedding model)
    Local chat model  (POST {MODEL_URL}/chat/completions,  e.g. qwen2.5:7b in Ollama, or vLLM)
    FAKE_LLM=1        no model server: hashing "embeddings" and an extractive answer (tests, smoke tests)

    GET  /            a tiny web page          GET /healthz   alive
    GET  /ready       model server reachable   POST /ask      {"question": "..."} -> answer + sources
Every question is written to an AUDIT LOG (JSON lines) on a local disk: on-prem customers usually require it.
"""
import hashlib
import json
import math
import os
import re
import time
from pathlib import Path

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

HERE = Path(__file__).parent
FAKE = os.getenv("FAKE_LLM", "") in {"1", "true", "yes"}
MODEL_URL = os.getenv("MODEL_URL", "http://ollama:11434/v1").rstrip("/")
CHAT_MODEL = os.getenv("CHAT_MODEL", "qwen2.5:7b")
EMBED_MODEL = os.getenv("EMBED_MODEL", "nomic-embed-text")
AUDIT_LOG = Path(os.getenv("AUDIT_LOG", "/data/audit.jsonl"))
KNOWLEDGE = Path(os.getenv("KNOWLEDGE_DIR", HERE / "knowledge"))
http = httpx.Client(timeout=300, trust_env=False)    # trust_env=False: never use a proxy from the environment


def chunks() -> list[dict]:
    """One chunk per '## ' section, with an id like cold-chain#logger-alarm-on-arrival for citations."""
    out = []
    for path in sorted(KNOWLEDGE.glob("*.md")):
        for section in re.split(r"\n(?=## )", path.read_text(encoding="utf-8")):
            if section.startswith("## "):
                title = section.splitlines()[0][3:].strip()
                out.append({"id": f"{path.stem}#{re.sub(r'[^a-z]+', '-', title.lower()).strip('-')}",
                            "title": title, "text": " ".join(section.splitlines()[1:]).strip()})
    return out


def fake_embed(text: str, dims: int = 256) -> list[float]:
    """Hashing trick: each word adds 1 to a slot chosen by its hash. Crude, but deterministic and offline."""
    v = [0.0] * dims
    for word in re.findall(r"[a-z0-9]+", text.lower()):
        v[int(hashlib.md5(word.encode()).hexdigest(), 16) % dims] += 1.0
    return v


def embed(texts: list[str]) -> list[list[float]]:
    if FAKE:
        return [fake_embed(t) for t in texts]
    r = http.post(f"{MODEL_URL}/embeddings", json={"model": EMBED_MODEL, "input": texts})
    r.raise_for_status()
    return [d["embedding"] for d in sorted(r.json()["data"], key=lambda d: d["index"])]


def cosine(a, b) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    return dot / ((math.sqrt(sum(x * x for x in a)) * math.sqrt(sum(y * y for y in b))) or 1.0)


class Index:
    def __init__(self):
        self.items = chunks()
        self.vectors = embed([c["title"] + ". " + c["text"] for c in self.items])

    def search(self, question: str, k: int = 3) -> list[dict]:
        q = embed([question])[0]
        scored = sorted(((cosine(q, v), c) for v, c in zip(self.vectors, self.items)), key=lambda p: -p[0])
        return [{**c, "score": round(s, 3)} for s, c in scored[:k]]


def answer(question: str, sources: list[dict]) -> str:
    if FAKE:
        best = sources[0]
        return f"(FAKE, extractive) {best['text']} [{best['id']}]"
    context = "\n\n".join(f"[{s['id']}] {s['title']}: {s['text']}" for s in sources)
    r = http.post(f"{MODEL_URL}/chat/completions", json={"model": CHAT_MODEL, "messages": [
        {"role": "system", "content": "Answer warehouse staff using ONLY the procedures below. Cite the [id] you used. "
                                      "If the procedures don't cover it, say so and tell them to ask the shift lead."},
        {"role": "user", "content": f"Procedures:\n{context}\n\nQuestion: {question}"}]})
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"]


def audit(entry: dict):
    AUDIT_LOG.parent.mkdir(parents=True, exist_ok=True)
    with AUDIT_LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


app = FastAPI(title="On-prem warehouse assistant")
_index = None


def index() -> Index:
    global _index
    if _index is None:
        _index = Index()
    return _index


class Question(BaseModel):
    question: str = Field(min_length=3, max_length=2000)
    user: str = "unknown"


@app.get("/healthz")
def healthz():
    return {"ok": True}


@app.get("/ready")
def ready():
    if FAKE:
        return {"ready": True, "mode": "fake"}
    try:
        models = http.get(f"{MODEL_URL}/models", timeout=5).json()
    except httpx.HTTPError as e:
        raise HTTPException(503, f"model server not reachable at {MODEL_URL}: {type(e).__name__}")
    names = [m["id"] for m in models.get("data", [])]
    missing = [m for m in (CHAT_MODEL, EMBED_MODEL) if not any(n.startswith(m) for n in names)]
    if missing:
        raise HTTPException(503, f"models not loaded: {missing} (have {names})")
    return {"ready": True, "mode": "local-model", "models": names}


@app.post("/ask")
def ask(q: Question):
    start = time.time()
    sources = index().search(q.question)
    text = answer(q.question, sources)
    audit({"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "user": q.user, "question": q.question,
           "sources": [s["id"] for s in sources], "answer_chars": len(text), "seconds": round(time.time() - start, 2),
           "model": "fake" if FAKE else CHAT_MODEL})
    return {"answer": text, "sources": [{"id": s["id"], "score": s["score"]} for s in sources]}


@app.get("/", response_class=HTMLResponse)
def page():
    return """<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Warehouse Assistant</title><style>body{font:16px system-ui,sans-serif;max-width:700px;margin:auto;padding:16px}
input,button{font:inherit;padding:8px}input{width:100%;box-sizing:border-box}pre{white-space:pre-wrap;background:#f3f3f3;padding:10px}
@media (prefers-color-scheme: dark){body{background:#151515;color:#eee}pre{background:#222}}</style></head><body>
<h1>Warehouse assistant (offline)</h1><p>Ask about warehouse procedures. Runs entirely on this site's servers.</p>
<input id="q" placeholder="A pallet arrived with the logger alarm on. What do I do?"><p><button id="b">Ask</button></p><pre id="a"></pre>
<script>document.getElementById('b').onclick=async()=>{const r=await fetch('/ask',{method:'POST',headers:{'Content-Type':'application/json'},
body:JSON.stringify({question:document.getElementById('q').value||document.getElementById('q').placeholder,user:'web'})});
const d=await r.json();document.getElementById('a').textContent=r.ok?d.answer+'\\n\\nSources: '+d.sources.map(s=>s.id).join(', '):JSON.stringify(d)};</script>
</body></html>"""
