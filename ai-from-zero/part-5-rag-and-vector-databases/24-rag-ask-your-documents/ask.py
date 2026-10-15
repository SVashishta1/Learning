# Ask questions about everything in the docs/ folder. Put your own PDFs or notes in docs/ first!
# Usage: python ask.py      (then type questions)     or     python ask.py "How many vacation days do I get?"
import sys

import rag


def ask_and_show(question):
    reply, sources = rag.answer(question)
    print(f"\n💬 {reply}\n")
    for n, s in enumerate(sources, start=1):            # show which chunks the answer was based on
        preview = s["text"][:80].replace("\n", " ")
        print(f"   [{n}] {s['source']}: {preview}...")
    print()


rag.add_folder("docs")
print(f"\n✅ {rag.library.count()} chunks stored in the vector database.\n")

if len(sys.argv) > 1:                                   # a question was typed after "python ask.py"
    ask_and_show(" ".join(sys.argv[1:]))
else:                                                   # no question given: keep asking until you press Enter
    while True:
        question = input("❓ Your question (Enter to quit): ").strip()
        if not question:
            break
        ask_and_show(question)
