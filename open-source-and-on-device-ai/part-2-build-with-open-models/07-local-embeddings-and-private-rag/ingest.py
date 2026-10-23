"""Step 1 of private RAG: read your documents, cut them into chunks, turn each chunk into numbers
(an embedding) with a LOCAL model, and save everything in a SQLite file. Nothing leaves your computer.

Run:  python ingest.py            (reads docs/, writes rag.db)
"""
import sqlite3
import sys
from pathlib import Path

import numpy as np
import ollama

EMBED_MODEL = "nomic-embed-text"
DOCS = Path(__file__).parent / "docs"
DB = Path(__file__).parent / "rag.db"
MAX_CHARS = 400  # roughly 100 tokens: small enough to be precise, big enough to keep a full idea


def chunk(text):
    """Split a document into paragraphs, then join short neighbours until a chunk is ~MAX_CHARS long."""
    lines = text.strip().splitlines()
    title = lines[0].lstrip("# ").strip() if lines and lines[0].startswith("#") else ""
    body = "\n".join(lines[1:] if title else lines)
    chunks, current = [], ""
    for para in [p.strip() for p in body.split("\n\n") if p.strip()]:
        if current and len(current) + len(para) > MAX_CHARS:
            chunks.append(current)
            current = para
        else:
            current = f"{current}\n\n{para}" if current else para
    if current:
        chunks.append(current)
    # Put the title in front of every chunk, so "30 days" still knows it is about *returns*.
    return [f"{title}: {c}" if title else c for c in chunks]


def main():
    files = sorted(list(DOCS.glob("*.md")) + list(DOCS.glob("*.txt")))
    if not files:
        sys.exit(f"No .md or .txt files in {DOCS}")

    rows = []  # (source file, chunk number, text)
    for f in files:
        for i, text in enumerate(chunk(f.read_text(encoding="utf-8")), start=1):
            rows.append((f.name, i, text))

    # nomic-embed-text was trained with a task prefix: "search_document: " for stored text.
    try:
        result = ollama.embed(model=EMBED_MODEL, input=["search_document: " + r[2] for r in rows])
    except ConnectionError:
        sys.exit("Can't reach Ollama. Open the Ollama app or run `ollama serve`.")
    except ollama.ResponseError as e:
        sys.exit(f"Ollama says: {e.error}  (try: ollama pull {EMBED_MODEL})")

    vectors = np.array(result.embeddings, dtype=np.float32)
    vectors /= np.linalg.norm(vectors, axis=1, keepdims=True)  # length 1, so similarity = a simple dot product

    DB.unlink(missing_ok=True)  # start fresh every time
    db = sqlite3.connect(DB)
    db.execute("CREATE TABLE chunks (id INTEGER PRIMARY KEY, source TEXT, chunk_no INTEGER, text TEXT, embedding BLOB)")
    db.executemany(
        "INSERT INTO chunks (source, chunk_no, text, embedding) VALUES (?, ?, ?, ?)",
        [(src, no, text, vec.tobytes()) for (src, no, text), vec in zip(rows, vectors)],
    )
    db.commit()
    db.close()
    print(f"Read {len(files)} files -> {len(rows)} chunks -> vectors of {vectors.shape[1]} numbers.")
    print(f"Saved to {DB.name} ({DB.stat().st_size / 1024:.0f} KB).")


if __name__ == "__main__":
    main()
