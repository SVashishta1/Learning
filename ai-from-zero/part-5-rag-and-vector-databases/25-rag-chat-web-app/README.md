# 25 · RAG chat web app

**What it does:** a web app where you **upload PDFs** and **chat with them**. Answers show their sources, and the chat remembers your previous questions, so follow-ups like "and what about hotels?" work.

## Run it
```bash
cd part-5-rag-and-vector-databases/25-rag-chat-web-app
uvicorn app:app --reload
```
Open http://127.0.0.1:8000:
1. Ask "What's the meal allowance when travelling?"
2. Follow up with "and for hotels in Paris?" (it remembers the topic)
3. Click **Upload** and add any PDF of yours, then ask about it.

## The idea in one sentence
This is project 24's RAG engine (`rag.py`, unchanged) plus chat memory from Part 4 plus a web page. That combination is what many companies are building right now.

## Try this
1. Upload a long PDF (a manual or a book chapter) and ask about something on its last page.
2. In `app.py`, change `history[-6:]` to `history[-2:]`. Follow-up questions get worse. Why?
