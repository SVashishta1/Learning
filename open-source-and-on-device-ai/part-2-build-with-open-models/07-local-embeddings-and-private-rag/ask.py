"""Step 2 of private RAG: find the chunks that match your question, and let a local LLM answer
using ONLY those chunks, with citations like [1] that point back to the source file.

Run:  python ask.py "How long do I have to return a bike?"
      python ask.py                 (ask several questions; empty line to quit)
"""
import sqlite3
import sys
from pathlib import Path

import numpy as np
import ollama

EMBED_MODEL = "nomic-embed-text"
CHAT_MODEL = "llama3.2:3b"
DB = Path(__file__).parent / "rag.db"
TOP_K = 3  # how many chunks to give the LLM

SYSTEM = """You answer questions for staff of a bike shop, using ONLY the numbered sources below.
After every fact, cite its source number in square brackets, like [1] or [2].
If the sources do not contain the answer, say "I don't know based on the documents." Do not guess."""


def load_index():
    if not DB.exists():
        sys.exit("rag.db not found. Run `python ingest.py` first.")
    db = sqlite3.connect(DB)
    rows = db.execute("SELECT source, chunk_no, text, embedding FROM chunks").fetchall()
    db.close()
    # Stack every stored vector into one big table of numbers: one row per chunk.
    matrix = np.stack([np.frombuffer(r[3], dtype=np.float32) for r in rows])
    return rows, matrix


def search(question, rows, matrix):
    """Return the TOP_K chunks most similar in meaning to the question, with their scores."""
    q = np.array(ollama.embed(model=EMBED_MODEL, input="search_query: " + question).embeddings[0], dtype=np.float32)
    q /= np.linalg.norm(q)
    scores = matrix @ q                          # one dot product per chunk = cosine similarity
    best = np.argsort(scores)[::-1][:TOP_K]      # positions of the highest scores, best first
    return [(rows[i], float(scores[i])) for i in best]


def answer(question, rows, matrix):
    hits = search(question, rows, matrix)
    sources = "\n\n".join(f"[{n}] {row[2]}" for n, (row, _) in enumerate(hits, start=1))
    response = ollama.chat(
        model=CHAT_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": f"Sources:\n{sources}\n\nQuestion: {question}"},
        ],
        options={"temperature": 0},  # facts, not creativity
    )
    print("\n" + response.message.content.strip())
    print("\nSources:")
    for n, ((source, chunk_no, _, _), score) in enumerate(hits, start=1):
        print(f"  [{n}] {source} (chunk {chunk_no}), similarity {score:.2f}")


def main():
    rows, matrix = load_index()
    try:
        if len(sys.argv) > 1:  # a question was typed after the file name
            answer(" ".join(sys.argv[1:]), rows, matrix)
        else:
            while question := input("\nQuestion (empty line to quit): ").strip():
                answer(question, rows, matrix)
    except (EOFError, KeyboardInterrupt):  # Ctrl+D / Ctrl+C: leave quietly
        print()
    except ConnectionError:
        sys.exit("Can't reach Ollama. Open the Ollama app or run `ollama serve`.")
    except ollama.ResponseError as e:
        sys.exit(f"Ollama says: {e.error}  (try: ollama pull {CHAT_MODEL} and ollama pull {EMBED_MODEL})")


if __name__ == "__main__":
    main()
