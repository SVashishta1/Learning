# Part 5 · RAG & vector databases

**RAG (Retrieval-Augmented Generation)** = before the AI answers, your code finds the most relevant pieces of *your own documents* and hands them to it. The AI then answers from your documents, with sources, instead of from memory.

To find "relevant" pieces you need **embeddings** (text turned into lists of numbers that capture meaning) and a **vector database** (a database that stores those number lists and finds the closest ones fast).

| # | Project | What you'll have |
|---|---------|------------------|
| 21 | [What is an embedding?](21-what-is-an-embedding) | see meaning turned into numbers |
| 22 | [Search by meaning](22-search-by-meaning) | a search that understands "money back" = "refund" |
| 23 | [Your first vector database (Chroma)](23-your-first-vector-database-chroma) | store, search, filter, update and delete |
| 24 | [RAG: ask your documents](24-rag-ask-your-documents) | AI answers from your PDFs and notes, with sources |
| 25 | [RAG chat web app](25-rag-chat-web-app) | upload a PDF in the browser and chat with it |
| 26 | [Production vector database (Postgres + pgvector)](26-production-vector-database-postgres) | the same RAG, on the database companies run in production |

Install once:
```bash
pip install chromadb numpy pypdf anthropic fastapi "uvicorn[standard]" python-multipart
```
The first time you run project 21, Chroma downloads a small embedding model (~80 MB). It runs on your own computer, free.
Projects 21–23 need **no API key**. Projects 24–26 use Claude (key setup is in the Part 4 README).
