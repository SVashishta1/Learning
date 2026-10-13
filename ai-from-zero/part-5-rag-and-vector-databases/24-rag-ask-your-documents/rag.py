# The RAG engine: READ documents → CUT them into chunks → STORE in Chroma → FIND relevant chunks → ASK Claude.
from pathlib import Path

import chromadb
from pypdf import PdfReader

import ai

db = chromadb.PersistentClient(path="chroma_data")
library = db.get_or_create_collection("my_documents", configuration={"hnsw": {"space": "cosine"}})


def read_file(path: Path) -> str:
    if path.suffix.lower() == ".pdf":
        return "\n".join(page.extract_text() or "" for page in PdfReader(path).pages)
    return path.read_text(encoding="utf-8", errors="ignore")


def cut_into_chunks(text: str, size: int = 500) -> list[str]:
    """Split text into pieces of about `size` characters, without cutting paragraphs in half when possible."""
    chunks, current = [], ""
    for paragraph in text.split("\n\n"):
        if len(current) + len(paragraph) > size and current:
            chunks.append(current.strip())
            current = ""
        current += paragraph + "\n\n"
    if current.strip():
        chunks.append(current.strip())
    return chunks


def add_document(path: Path) -> int:
    chunks = cut_into_chunks(read_file(path))
    library.upsert(ids=[f"{path.name}-{i}" for i in range(len(chunks))],     # same id again = replace, not duplicate
                   documents=chunks,
                   metadatas=[{"source": path.name} for _ in chunks])
    return len(chunks)


def add_folder(folder: str = "docs"):
    for path in sorted(Path(folder).iterdir()):
        if path.suffix.lower() in {".txt", ".md", ".pdf"}:
            print(f"📄 {path.name}: {add_document(path)} chunks")


def find_relevant(question: str, how_many: int = 4) -> list[dict]:
    found = library.query(query_texts=[question], n_results=min(how_many, library.count()))
    return [{"text": text, "source": meta["source"]} for text, meta in zip(found["documents"][0], found["metadatas"][0])]


RULES = """Answer the question using ONLY the numbered sources.
Put the source number after each fact, like [1].
If the sources don't contain the answer, say "I couldn't find that in your documents." Keep it short."""


def answer(question: str, conversation: list | None = None) -> tuple[str, list[dict]]:
    sources = find_relevant(question)
    numbered = "\n\n".join(f"[{n}] (from {s['source']})\n{s['text']}" for n, s in enumerate(sources, start=1))
    prompt = f"<sources>\n{numbered}\n</sources>\n\nQuestion: {question}"
    messages = (conversation or []) + [{"role": "user", "content": prompt}]
    return ai.ask(messages, system=RULES), sources
