# Ask questions about everything in the docs/ folder. Put your own PDFs or notes in docs/ first!
# Usage: python ask.py      (then type questions)     or     python ask.py "How many vacation days do I get?"
import sys

import rag

rag.add_folder("docs")
print(f"\n✅ {rag.library.count()} chunks stored in the vector database.\n")

questions = sys.argv[1:]
while True:
    question = questions.pop(0) if questions else (None if sys.argv[1:] else input("❓ Your question (Enter to quit): ").strip())
    if not question:
        break
    reply, sources = rag.answer(question)
    print(f"\n💬 {reply}\n")
    for n, s in enumerate(sources, start=1):
        print(f"   [{n}] {s['source']}: {s['text'][:80]}...")
    print()
