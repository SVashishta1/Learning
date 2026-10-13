# The same RAG as project 24, but the vectors live in PostgreSQL + pgvector: the database many companies already run.
# Usage: docker compose up -d   then   python pg_rag.py "What is the hotel limit in Paris?"
import os
import sys
from pathlib import Path

import psycopg
from chromadb.utils.embedding_functions import DefaultEmbeddingFunction

import ai

embed = DefaultEmbeddingFunction()                  # same free local model as before: 384 numbers per text
db = psycopg.connect(os.getenv("DATABASE_URL", "postgresql://rag:rag@localhost:5432/rag"), autocommit=True)

# 1. SET UP: switch on pgvector and make a table with a column of type vector(384)
db.execute("CREATE EXTENSION IF NOT EXISTS vector")
db.execute("""CREATE TABLE IF NOT EXISTS chunks (
                  id SERIAL PRIMARY KEY,
                  source TEXT,
                  content TEXT,
                  embedding vector(384))""")
# An HNSW index makes similarity search fast even with millions of rows
db.execute("CREATE INDEX IF NOT EXISTS chunks_embedding_idx ON chunks USING hnsw (embedding vector_cosine_ops)")


def as_vector(numbers) -> str:
    return "[" + ",".join(f"{x:.6f}" for x in numbers) + "]"     # pgvector's text format: [0.1,0.2,...]


def add_folder(folder="docs"):
    db.execute("DELETE FROM chunks")                                # start fresh each run (simple for learning)
    for path in sorted(Path(folder).glob("*.md")) + sorted(Path(folder).glob("*.txt")):
        pieces = [p.strip() for p in path.read_text().split("\n\n") if p.strip()]
        for piece, vector in zip(pieces, embed(pieces)):
            db.execute("INSERT INTO chunks (source, content, embedding) VALUES (%s, %s, %s::vector)",
                       (path.name, piece, as_vector(vector)))
        print(f"📄 {path.name}: {len(pieces)} chunks")


def find_relevant(question, how_many=4):
    q = as_vector(embed([question])[0])
    # <=> is pgvector's "cosine distance" operator: smaller = more similar. It's plain SQL!
    rows = db.execute("""SELECT source, content, 1 - (embedding <=> %s::vector) AS similarity
                         FROM chunks ORDER BY embedding <=> %s::vector LIMIT %s""", (q, q, how_many)).fetchall()
    return [{"source": s, "text": t, "similarity": round(sim, 2)} for s, t, sim in rows]


if __name__ == "__main__":
    add_folder()
    question = " ".join(sys.argv[1:]) or "What is the hotel limit in Paris, and how fast must I submit receipts?"
    sources = find_relevant(question)
    for s in sources:
        print(f"   {s['similarity']}  [{s['source']}] {s['text'][:70].replace(chr(10), ' ')}...")
    numbered = "\n\n".join(f"[{n}] {s['text']}" for n, s in enumerate(sources, start=1))
    print("\n💬", ai.ask(f"<sources>\n{numbered}\n</sources>\n\nQuestion: {question}",
                         system="Answer using ONLY the numbered sources and cite them like [1]. If they don't contain the answer, say so."))
