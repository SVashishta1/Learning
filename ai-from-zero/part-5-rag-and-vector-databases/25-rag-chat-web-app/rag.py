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
    pieces = []
    for paragraph in text.split("\n\n"):               # a blank line = a new paragraph
        while len(paragraph) > size:                    # too long (PDFs often have no blank lines): cut at a space
            cut = paragraph.rfind(" ", 0, size)
            cut = cut if cut > 0 else size
            pieces.append(paragraph[:cut])
            paragraph = paragraph[cut:].lstrip()
        pieces.append(paragraph)

    chunks, current = [], ""
    for piece in pieces:                                # glue small pieces together until a chunk is full
        if len(current) + len(piece) > size and current.strip():
            chunks.append(current.strip())
            current = ""
        current += piece + "\n\n"
    if current.strip():
        chunks.append(current.strip())
    return chunks


def add_document(path: Path) -> int:
    chunks = cut_into_chunks(read_file(path))
    library.delete(where={"source": path.name})        # forget this file's old chunks (it may have changed)
    if chunks:                                          # a scanned PDF (only pictures, no text) gives 0 chunks
        library.upsert(ids=[f"{path.name}-{i}" for i in range(len(chunks))],
                       documents=chunks,
                       metadatas=[{"source": path.name} for _ in chunks])
    return len(chunks)


def add_folder(folder: str = "docs"):
    for path in sorted(Path(folder).iterdir()):
        if path.suffix.lower() in {".txt", ".md", ".pdf"}:
            print(f"📄 {path.name}: {add_document(path)} chunks")


def find_relevant(question: str, how_many: int = 4) -> list[dict]:
    if library.count() == 0:                            # empty library: nothing to search
        return []
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
