"""CLI:  python ask.py                         (interactive)
        python ask.py "How many vacation days do I get?"
Put your own PDFs/markdown into ./docs first."""
import sys

import llm
from rag import Embedder, Index, answer

index = Index(Embedder()).build("docs")
index.save()
print(f"Indexed {len(index.chunks)} chunks with the '{index.embedder.backend}' embedder.\n")
client = llm.get_client()
questions = sys.argv[1:]
while True:
    try:
        q = questions.pop(0) if questions else (None if sys.argv[1:] else input("question> ").strip())
    except (EOFError, KeyboardInterrupt):      # Ctrl+D / Ctrl+C: leave quietly
        break
    if not q:
        break
    result = answer(client, index, q)
    print("\n" + result["answer"])
    for s in result["sources"]:
        print(f"   [{s['n']}] {s['source']} (similarity {s['score']})")
    print()
