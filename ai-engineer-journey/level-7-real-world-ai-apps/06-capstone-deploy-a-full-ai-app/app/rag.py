"""Project 7.3: Retrieval-Augmented Generation (RAG), built from parts you understand.

INGEST:   documents -> text -> chunks -> embeddings -> index (saved to disk)
ASK:      question -> embedding -> top-k similar chunks -> prompt with numbered sources -> Claude -> cited answer
"""
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np

from app import llm


# ---------------- 1. Load documents ----------------
def load_documents(folder: str) -> list[tuple[str, str]]:
    docs = []
    for path in sorted(Path(folder).rglob("*")):
        if path.suffix.lower() in {".md", ".txt"}:
            docs.append((path.name, path.read_text(encoding="utf-8")))
        elif path.suffix.lower() == ".pdf":
            from pypdf import PdfReader
            for i, page in enumerate(PdfReader(path).pages, start=1):
                docs.append((f"{path.name} p.{i}", page.extract_text() or ""))
    return docs


# ---------------- 2. Chunk ----------------
@dataclass
class Chunk:
    id: int
    source: str
    text: str


def chunk_text(text: str, size: int = 600, overlap: int = 120) -> list[str]:
    """Split into ~size-character chunks on sentence boundaries, with overlap so facts aren't cut in half."""
    sentences = re.split(r"(?<=[.!?])\s+|\n{2,}", text)
    chunks, current = [], ""
    for s in filter(None, (s.strip() for s in sentences)):
        if current and len(current) + len(s) > size:
            chunks.append(current.strip())
            current = current[-overlap:]           # carry the tail of the previous chunk forward
        current += " " + s
    if current.strip():
        chunks.append(current.strip())
    return chunks


# ---------------- 3. Embed ----------------
class Embedder:
    """Uses a real sentence-embedding model if installed, otherwise TF-IDF (keyword-based) so the project still runs."""
    def __init__(self, backend: str = "auto"):
        self.backend = backend
        if backend in ("auto", "sentence-transformers"):
            try:
                from sentence_transformers import SentenceTransformer
                self.model = SentenceTransformer("all-MiniLM-L6-v2")
                self.backend = "sentence-transformers"
            except Exception:
                if backend != "auto":
                    raise
                self.backend = "tfidf"
        self.vectorizer = None

    def fit(self, texts):
        if self.backend == "tfidf":
            from sklearn.feature_extraction.text import TfidfVectorizer
            self.vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2), sublinear_tf=True).fit(texts)
        return self

    def encode(self, texts) -> np.ndarray:
        if self.backend == "sentence-transformers":
            return self.model.encode(texts, normalize_embeddings=True)
        v = self.vectorizer.transform(texts).toarray()
        return v / (np.linalg.norm(v, axis=1, keepdims=True) + 1e-9)


# ---------------- 4. Index (a tiny vector database) ----------------
class Index:
    def __init__(self, embedder: Embedder):
        self.embedder, self.chunks, self.vectors = embedder, [], None

    def build(self, folder: str, size=600, overlap=120):
        for source, text in load_documents(folder):
            for piece in chunk_text(text, size, overlap):
                self.chunks.append(Chunk(len(self.chunks), source, piece))
        self.embedder.fit([c.text for c in self.chunks])
        self.vectors = self.embedder.encode([c.text for c in self.chunks])
        return self

    def search(self, query: str, k: int = 4) -> list[tuple[Chunk, float]]:
        sims = self.vectors @ self.embedder.encode([query])[0]      # cosine similarity (vectors are unit length)
        top = sims.argsort()[::-1][:k]
        return [(self.chunks[i], float(sims[i])) for i in top]

    def save(self, folder="index"):
        Path(folder).mkdir(exist_ok=True)
        np.save(f"{folder}/vectors.npy", self.vectors)
        Path(f"{folder}/chunks.json").write_text(json.dumps([asdict(c) for c in self.chunks], indent=1))


# ---------------- 5. Generate ----------------
SYSTEM = """You answer questions about company documents.
Rules:
- Use ONLY the numbered sources provided. If they don't contain the answer, say "I couldn't find that in the documents."
- Cite sources inline like [1] or [2][3] after each fact.
- Be concise."""


def answer(client, index: Index, question: str, k: int = 4) -> dict:
    hits = index.search(question, k)
    sources = "\n\n".join(f"[{n}] (from {c.source})\n{c.text}" for n, (c, _) in enumerate(hits, start=1))
    response = llm.create(client, max_tokens=1500, system=SYSTEM, output_config={"effort": "low"},
                          messages=[{"role": "user", "content": f"<sources>\n{sources}\n</sources>\n\nQuestion: {question}"}])
    text = llm.text_of(response)
    cited = sorted({int(n) for n in re.findall(r"\[(\d+)\]", text) if 0 < int(n) <= len(hits)})
    return {"answer": text,
            "sources": [{"n": n, "source": hits[n - 1][0].source, "score": round(hits[n - 1][1], 3), "text": hits[n - 1][0].text} for n in cited],
            "retrieved": [c.source for c, _ in hits],
            "usage": {"input_tokens": response.usage.input_tokens, "output_tokens": response.usage.output_tokens}}
