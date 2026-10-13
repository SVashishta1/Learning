# 7.3 · RAG: ask questions about your PDFs

**What you build:** a **Retrieval-Augmented Generation** app. Drop PDFs or notes into `docs/` and ask questions in plain English. It finds the most relevant passages, gives them to Claude, and returns an answer **with citations** like `[1]`, plus a CLI and an API with upload.
It ships with a fake company handbook (vacation, expenses, IT security) so it works immediately.

**Like you're 10:** an open-book exam. The AI doesn't need to *memorise* your documents. Before answering, a librarian (retrieval) quickly finds the 4 most relevant pages and puts them on the desk. The AI answers using only those pages and points at which page each fact came from.

## Run it
```bash
cd level-7-real-world-ai-apps/03-rag-ask-questions-about-your-pdfs
pip install -r requirements.txt               # sentence-transformers downloads a ~90 MB model once
export ANTHROPIC_API_KEY=sk-ant-...
python ask.py "How many vacation days can I carry over, and until when?"
python ask.py                                  # interactive mode
uvicorn app:app --reload                       # API: POST /ask, POST /documents (upload a PDF)
```
Try a question the docs *don't* answer ("What's the CEO's salary?"). It should say it couldn't find it instead of making something up.

Tests (offline): `pytest -v`

## The pipeline (all in `rag.py`, ~120 lines)
| Step | Function | Notes |
|------|----------|-------|
| Load | `load_documents` | .md, .txt and .pdf (one entry per page, so citations show page numbers) |
| Chunk | `chunk_text` | ~600 characters on sentence boundaries, 120-character overlap |
| Embed | `Embedder` | `all-MiniLM-L6-v2` (meaning-based, from 5.4); TF-IDF fallback if not installed |
| Index | `Index.search` | cosine similarity over a NumPy matrix: a tiny vector database |
| Generate | `answer` | numbered sources in the prompt, strict rules in the system prompt, citations parsed back |

## Key ideas
- **Why RAG instead of fine-tuning?** Facts change. RAG updates the moment you add a file, cites its sources, and costs nothing to "train".
- **Chunk size is a real trade-off:** too small and facts lose context; too large and retrieval gets fuzzy and prompts get expensive. You'll measure this in 7.5.
- **Grounding rules** in the system prompt ("only use the sources", "say you couldn't find it") are what fight hallucination.
- **At scale** you'd swap the NumPy index for a vector database (Chroma, pgvector, Pinecone, OpenSearch) and add *hybrid search* (keywords + embeddings) and *re-ranking*.

## Your turn
1. Add your own PDFs (lecture notes, a manual) and ask 10 questions. Note which ones fail and why: retrieval or generation?
2. Replace the NumPy index with **Chroma** (`pip install chromadb`), a real vector database, in ~15 lines.
3. Add **hybrid search**: combine the TF-IDF and embedding scores (e.g. 0.3 / 0.7) and see whether retrieval improves.

## Read / watch
- RAG explained: https://www.youtube.com/results?search_query=retrieval+augmented+generation+RAG+explained
- Contextual Retrieval (Anthropic): https://www.anthropic.com/news/contextual-retrieval
