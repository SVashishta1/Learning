# Part 5 · RAG & vector databases

**RAG (Retrieval-Augmented Generation)** = before the AI answers, your code finds the most relevant pieces of *your own documents* and hands them to it. The AI then answers from your documents, with sources, instead of from memory.

To find "relevant" pieces you need **embeddings** (text turned into lists of numbers that capture meaning) and a **vector database** (a database that stores those number lists and finds the closest ones fast).

```
your question ──► embedding ──► vector database ──► 4 closest chunks ──► Claude ──► answer with [1] [2] sources
```

| # | Project | What you'll have | Needs |
|---|---------|------------------|-------|
| 21 | [What is an embedding?](21-what-is-an-embedding) | see meaning turned into numbers | nothing extra |
| 22 | [Search by meaning](22-search-by-meaning) | a search that understands "money back" = "refund" | nothing extra |
| 23 | [Your first vector database (Chroma)](23-your-first-vector-database-chroma) | store, search, filter, update and delete | nothing extra |
| 24 | [RAG: ask your documents](24-rag-ask-your-documents) | AI answers from your PDFs and notes, with sources | API key |
| 25 | [RAG chat web app](25-rag-chat-web-app) | upload a PDF in the browser and chat with it | API key |
| 26 | [Production vector database (Postgres + pgvector)](26-production-vector-database-postgres) | the same RAG, on the database companies run in production | API key + Docker |

**Time:** about 1–2 weeks at 1 hour a day.

## Install once
With your virtual environment switched on (see [00 · Start here](../00-start-here)):
```bash
pip install chromadb numpy pypdf anthropic fastapi "uvicorn[standard]" python-multipart
```
- `chromadb`: the vector database, plus a small free embedding model
- `numpy`: fast maths on lists of numbers
- `pypdf`: reads the text out of PDF files
- `anthropic`: talks to Claude
- `fastapi`, `uvicorn[standard]`, `python-multipart`: the web app and its file uploads (project 25)

Project 26 also needs `pip install "psycopg[binary]"` and Docker Desktop. Its README walks you through it.

The first time you run project 21, Chroma downloads a small embedding model (about 80 MB). After that it runs on your own computer, free and offline.

Projects 21–23 need **no API key**. Projects 24–26 use Claude: set `ANTHROPIC_API_KEY` as shown in the [Part 4 README](../part-4-chatbots).

## Next
After project 26, continue with [Part 6 · AI agents & teams](../part-6-ai-agents-and-teams).
