# 24 · RAG: ask your documents

**What it does:** reads every PDF, text and markdown file in the `docs/` folder, stores them in a vector database, and answers your questions **using only your documents**, with sources like `[1]`. It comes with a sample company handbook (holidays, expenses, IT rules).

## Run it
```bash
cd part-5-rag-and-vector-databases/24-rag-ask-your-documents
python ask.py "How many vacation days can I carry over, and until when?"
python ask.py          # ask as many questions as you like
```
Now drop **your own PDFs** (lecture notes, a manual, a contract) into `docs/` and ask about them!

Ask something that's NOT in the documents ("What's the CEO's salary?"). It should say it couldn't find it instead of inventing an answer.

## How it works (5 steps, all in `rag.py`)
1. **Read** the files (PDFs too).
2. **Cut** them into ~500-character chunks.
3. **Store** the chunks in Chroma (embeddings are made automatically).
4. **Find** the 4 chunks closest in meaning to your question.
5. **Ask** Claude to answer using only those chunks, and cite them.

## Try this
1. Change `size=500` to `200` and to `1500` in `cut_into_chunks`. Do answers get better or worse?
2. Change `how_many=4` to `1`. When does it miss information?
3. Remove the "say you couldn't find it" rule from `RULES` and ask about the CEO's salary again.
