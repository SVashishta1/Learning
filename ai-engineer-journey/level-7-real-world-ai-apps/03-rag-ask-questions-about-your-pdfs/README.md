# 7.3 · RAG: ask questions about your PDFs

**What you'll build:** a **Retrieval-Augmented Generation** (RAG) app. Drop PDFs or notes into `docs/` and ask questions in plain English. It finds the most relevant passages, gives them to Claude, and returns an answer **with citations** like `[1]`. You get a CLI and an API with upload. It ships with a fake company handbook (vacation, expenses, IT security) so it works immediately.
**Like you're 10:** an open-book exam. The AI doesn't need to *memorise* your documents. Before answering, a librarian (retrieval) quickly finds the 4 most relevant pages and puts them on the desk. The AI answers using only those pages and points at which page each fact came from.
**Time:** ~3 h · **Builds on:** [7.2 Structured data extractor](../02-structured-data-extractor-invoices-to-json) and [5.4 Embeddings](../../level-5-text-models/04-embeddings-find-similar-sentences) · **Needs:** an Anthropic API key (tests run without one); internet once for the ~90 MB embedding model

## Why this matters
"Chat with our documents" is the most requested AI feature in companies: HR handbooks, product manuals, legal contracts, support knowledge bases. A model alone doesn't know your private documents and will confidently guess. RAG fixes that by looking things up first and showing where each fact came from. Chunking, embeddings, vector search and grounded prompts are core skills in almost every AI engineering job posting.

## What you'll learn
- **RAG**: retrieve relevant text first, then let the model answer from it ("open book" instead of "from memory").
- **Chunking**: cutting documents into small overlapping pieces so search can find the exact passage.
- **Embeddings + cosine similarity**: turning text into vectors so "time off" matches "vacation" by meaning, not just by words.
- **Vector index**: a table of chunk vectors you can search quickly (here a NumPy matrix, in production a vector database).
- **Grounding and citations**: system-prompt rules that make the model use only the sources and say when it can't find the answer.

## Before you start
```bash
cd level-7-real-world-ai-apps/03-rag-ask-questions-about-your-pdfs
pip install -r requirements.txt
```
- `anthropic`: calls Claude.
- `numpy`: the vector maths and the index.
- `sentence-transformers`: the meaning-based embedding model `all-MiniLM-L6-v2` (it also installs PyTorch, a big download the first time).
- `scikit-learn`: TF-IDF, the keyword-based fallback embedder.
- `pypdf`: reads text out of PDFs.
- `fastapi`, `uvicorn[standard]`, `python-multipart`: the API with file upload.
- `httpx`, `pytest`: tests.

**API key:** set `ANTHROPIC_API_KEY` as in the [Level 7 README](../README.md#api-key-needed-from-here-on). Tests need no key and no internet.

## Run it
1. From the course root: `cd level-7-real-world-ai-apps/03-rag-ask-questions-about-your-pdfs`
2. Tests (offline): `pytest -v`
3. Ask one question: `python ask.py "How many vacation days can I carry over, and until when?"`
4. Interactive mode: `python ask.py` (empty line or Ctrl+C to quit). Try a question the docs *don't* answer: "What's the CEO's salary?"
5. API: `uvicorn app:app --reload`, then at http://127.0.0.1:8000/docs try `POST /ask` with `{"question": "What is the hotel limit in Paris?"}`, upload a PDF with `POST /documents`, and list files with `GET /documents`.

### What you should see
(Claude's wording and the similarity numbers vary a little.)
```
Indexed 6 chunks with the 'sentence-transformers' embedder.


You can carry over up to 5 unused vacation days into the next year [1]. They must be used before March 31, or they expire [1].
   [1] vacation_policy.md (similarity 0.584)
```
And for "What's the CEO's salary?":
```
I couldn't find that in the documents.
```
What to look at:
- **`[1]`** in the answer matches the source list below it. You can check the fact yourself in `docs/vacation_policy.md`.
- The made-up-salary question gets an honest "couldn't find", not an invented number. That's the grounding rule working.
- If you see `(No sentence-transformers model: ... Falling back to TF-IDF keyword search.)` and `'tfidf' embedder`, the embedding model couldn't be loaded (usually no internet on the first run). It still works, but matches words rather than meaning, so similarity scores are lower (~0.2).
- An `index/` folder appears with `vectors.npy` and `chunks.json`. Open `chunks.json` to see exactly how your documents were cut up.

## How it works
```
INGEST (once):  docs/*.md|txt|pdf ─► load_documents ─► chunk_text ─► Embedder.encode ─► Index (matrix of vectors)
ASK (each question):
   question ─► encode ─► Index.search: cosine similarity with every chunk ─► top 4 chunks
           ─► prompt: <sources>[1]...[4]</sources> + question ─► Claude (SYSTEM rules) ─► answer with [n] ─► citations parsed
```
All the logic lives in `rag.py` (~120 lines), in five numbered sections:

1. **`load_documents(folder)`** walks `docs/` and returns `(source, text)` pairs. `.md`/`.txt` files are read whole; PDFs are read page by page with `pypdf`, named like `manual.pdf p.3`, so citations can point to a page.
2. **`chunk_text(text, size=600, overlap=120)`** splits text into sentences (a regex that cuts after `.`, `!`, `?` or at blank lines) and packs them into ~600-character chunks. When a chunk is full, the last 120 characters are carried into the next one (`current[-overlap:]`), so a fact sitting on a border isn't cut in half. Each piece becomes a `Chunk(id, source, text)`.
3. **`Embedder`** turns text into vectors. With `backend="auto"` it tries `SentenceTransformer("all-MiniLM-L6-v2")` (384 numbers per text, meaning-based, as in 5.4); if that fails it prints a note and uses TF-IDF (word-count based). `encode()` always returns vectors of length 1 ("normalised"), so a simple dot product equals the cosine similarity.
4. **`Index`** is a tiny vector database. `build()` chunks every document and stores all vectors in one matrix (`self.vectors`, one row per chunk). `search(query, k)` encodes the question and computes `self.vectors @ query_vector`: one similarity score per chunk in a single line. `argsort()[::-1][:k]` picks the top k. `save()` writes the index to `index/` so you can inspect it.
5. **`answer(client, index, question, k=4)`** numbers the top chunks as `[1] (from file)\n text`, wraps them in `<sources>` tags, and sends them with the question. The `SYSTEM` prompt says: use ONLY the sources, otherwise say "I couldn't find that", and cite like `[1]`. After the reply, a regex finds every `[n]` in the text and returns only the sources that were actually cited, plus what was retrieved and the token usage.

The other files:
- **`ask.py`** builds the index, prints how many chunks it made and which embedder it used, then answers questions from the command line or interactively.
- **`app.py`** builds the index once at startup. `POST /ask` answers; `POST /documents` saves an uploaded `.pdf`/`.md`/`.txt` into `docs/` (only the file name is kept, so a sneaky name like `../../x` can't write elsewhere) and rebuilds the index, which is fine for small collections.
- **`test_rag.py`** uses the TF-IDF embedder (offline, deterministic) to check chunk sizes and overlap, that retrieval finds the right document for three questions, and that `answer()` sends numbered sources and parses citations, using `FakeClient`.

Why RAG instead of fine-tuning (6.3)? Facts change. RAG updates the moment you add a file, shows its sources, and costs nothing to "train". Fine-tuning is for style and format.

## If something goes wrong
- **`'tfidf' embedder` when you expected sentence-transformers** → the model download failed or the package isn't installed. Check your internet, run `pip install sentence-transformers`, and run again (the model is cached after the first success).
- **Answers say "I couldn't find that" for things that ARE in your PDF** → the PDF may be a scanned image with no text layer (`pypdf` can only read real text). Open `index/chunks.json`: if your text isn't there, the PDF needs OCR first. Also try asking with words used in the document, or raise `k`.
- **`anthropic.AuthenticationError`** → set `ANTHROPIC_API_KEY` in this terminal.
- **`Upload a .pdf, .md or .txt file` (400)** → only those three types are indexed. Convert Word files to PDF first.
- **The API is slow after each upload** → it re-embeds every document each time. Fine for a handful of files; for many, see *Try this* 2.

## Try this
1. **Tune the retrieval.** Ask 5 questions with `k=1`, then `k=8` (`answer(client, index, q, k=8)` in `ask.py`), and try `chunk_text` with `size=200`. Which settings give the best answers? Which use the most tokens?
   <details><summary>Hint</summary>

   `result["usage"]["input_tokens"]` shows the prompt size. Bigger `k` and bigger chunks mean more context (better recall, but more tokens and more chance of distracting text). Tiny chunks lose context ("it must be used before March 31": what must?). You'll measure this properly in 7.5.
   </details>
2. **Use a real vector database.** Store the chunks in **Chroma** (`pip install chromadb`), which saves to disk so you don't re-embed everything on every start.
   <details><summary>Solution</summary>

   ```python
   import chromadb
   from rag import Embedder, Index

   index = Index(Embedder()).build("docs")
   db = chromadb.PersistentClient(path="chroma_db")                     # a folder on disk
   col = db.get_or_create_collection("docs", metadata={"hnsw:space": "cosine"})
   col.upsert(ids=[str(c.id) for c in index.chunks],
              documents=[c.text for c in index.chunks],
              metadatas=[{"source": c.source} for c in index.chunks],
              embeddings=index.vectors.tolist())                         # our own vectors

   question = "How long must passwords be?"
   res = col.query(query_embeddings=index.embedder.encode([question]).tolist(), n_results=4)
   for meta, dist in zip(res["metadatas"][0], res["distances"][0]):
       print(meta["source"], round(1 - dist, 3))                         # Chroma returns distance = 1 - similarity
   ```
   Next run, skip `build()`/`upsert()` and just `query()`. pgvector (Postgres) and Pinecone work the same way.
   </details>
3. **Hybrid search.** Combine meaning (embeddings) and keywords (TF-IDF) with weights 0.7 / 0.3. Keywords help with exact terms like product codes or "MFA".
   <details><summary>Solution</summary>

   ```python
   from rag import Embedder, Index

   class HybridIndex(Index):
       def __init__(self):
           super().__init__(Embedder("sentence-transformers"))
           self.keywords = Embedder("tfidf")

       def build(self, folder, size=600, overlap=120):
           super().build(folder, size, overlap)
           self.keywords.fit([c.text for c in self.chunks])
           self.kw_vectors = self.keywords.encode([c.text for c in self.chunks])
           return self

       def search(self, query, k=4):
           sims = (0.7 * (self.vectors @ self.embedder.encode([query])[0])
                   + 0.3 * (self.kw_vectors @ self.keywords.encode([query])[0]))
           top = sims.argsort()[::-1][:k]
           return [(self.chunks[i], float(sims[i])) for i in top]
   ```
   Use `HybridIndex().build("docs")` in `ask.py` instead of `Index(Embedder()).build("docs")`.
   </details>

## Check yourself
1. Why split documents into chunks instead of sending whole documents to Claude?
2. Why does `chunk_text` overlap neighbouring chunks?
3. The answer is wrong. How do you tell whether retrieval or generation failed?
4. Your HR policy changes next week. What do you need to do with RAG? What would you need to do with a fine-tuned model?

<details><summary>Answers</summary>

1. Search becomes precise (find the one paragraph that matters), prompts stay small and cheap, and the model isn't distracted by pages of unrelated text. With hundreds of documents, they wouldn't fit anyway.
2. So a fact near a chunk border still appears whole in at least one chunk.
3. Look at `retrieved` / the sources: if the right passage isn't among them, retrieval failed (fix chunking, embeddings, `k`). If it is there and the answer is still wrong, generation failed (fix the prompt or model).
4. RAG: replace the file in `docs/` and rebuild the index; the next answer uses the new policy. Fine-tuned: build a new training set and retrain, and the model could still mix up old and new facts.
</details>

## Learn more (optional)
- RAG explained: https://www.youtube.com/results?search_query=retrieval+augmented+generation+RAG+explained
- Contextual Retrieval (Anthropic): https://www.anthropic.com/news/contextual-retrieval
- Sentence-Transformers docs: https://sbert.net/

## Next
→ [7.4 · AI agent with tools (calculator, weather, web search)](../04-ai-agent-with-tools-calculator-weather-search)
