# 25 · RAG chat web app

**What you'll build:** a web page where you **upload PDFs** and **chat with them**. Every answer shows its sources, and the chat remembers your previous questions, so follow-ups like "and for hotels in Paris?" work.
**Time:** ~1 hour · **Builds on:** [24 · RAG: ask your documents](../24-rag-ask-your-documents) and [19 · Chatbot with a web page](../../part-4-chatbots/19-chatbot-with-a-web-page) · **Needs:** an Anthropic API key

## Why this matters
This is lesson 24's RAG engine (`rag.py`, the same file) plus chat memory from Part 4 plus a web page. That combination, "chat with your company's documents", is one of the most common AI products companies are building right now. After this lesson you have a working version you can show someone.

## What you'll learn
- **Web API around RAG:** the browser sends questions to your Python server (FastAPI), which runs RAG and sends back the answer and its sources as JSON.
- **File upload:** the browser sends a PDF to the server, which saves it and adds it to the vector database straight away.
- **Chat memory per user:** each browser tab gets its own `chat_id`, so two tabs have two separate conversations.
- **Short memory window:** only the last 3 question/answer pairs are sent to the AI, to keep requests small and cheap.

## Before you start
- Install the Part 5 packages (once):
  ```bash
  pip install chromadb numpy pypdf anthropic fastapi "uvicorn[standard]" python-multipart
  ```
  Used here: `fastapi` (the web server), `uvicorn` (runs it), `python-multipart` (lets FastAPI receive uploaded files), plus `chromadb`, `pypdf` and `anthropic` as in lesson 24.
- Set your API key in the terminal you'll use (full steps in the [Part 4 README](../../part-4-chatbots)):
  ```bash
  export ANTHROPIC_API_KEY=sk-ant-your-key-here        # Mac
  $env:ANTHROPIC_API_KEY="sk-ant-your-key-here"        # Windows PowerShell
  ```

## Run it
1. From the course folder (`Learning/ai-from-zero`), with your venv switched on:
   ```bash
   cd part-5-rag-and-vector-databases/25-rag-chat-web-app
   uvicorn app:app --reload
   ```
2. Open http://127.0.0.1:8000 in your browser.
3. Ask `What's the meal allowance when travelling?`
4. Follow up with `and for hotels in Paris?`, then `Explain your last answer in one simple sentence.` (it remembers the conversation).
5. Click **⬆ Upload PDF / TXT / MD**, choose any PDF of yours, then ask about it.
6. To stop the server, press `Ctrl + C` in the terminal.

### What you should see
In the terminal:
```
📄 expense_policy.md: 2 chunks
📄 it_security.md: 3 chunks
📄 vacation_policy.md: 3 chunks
INFO:     Started server process [5346]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
```
In the browser: a green header listing `In the library: expense_policy.md, it_security.md, vacation_policy.md`, and a chat. A conversation looks like this (Claude's wording will differ):
```
You:  What's the meal allowance when travelling?
Bot:  While travelling, meals are reimbursed up to 60 euros per day [1]. Alcohol is never reimbursed [1].
      Sources: [1] expense_policy.md  [2] expense_policy.md  [3] vacation_policy.md  [4] vacation_policy.md
You:  and for hotels in Paris?
Bot:  Hotels in Paris are reimbursed up to 180 euros per night, because Paris counts as a major city [1].
```
After an upload you'll see `Added your_file.pdf (12 chunks). Ask me about it!` and the file name appears in the header.

## How it works
```
browser (page.html) ──POST /ask {chat_id, text}──► app.py ──► rag.answer() ──► Chroma + Claude
                    ◄──── {reply, sources} ────────┘
browser ──POST /upload (a file)──► app.py ──► saves to docs/ ──► rag.add_document()
```
1. When the server starts, `rag.add_folder("docs")` loads every file in `docs/` into the vector database (that's the `📄` lines).
2. `chats` is a dictionary: `chat_id → list of messages`. It lives in the server's memory, so it is empty again after a restart.
3. `POST /ask` (`ask(q)`): `chats.setdefault(q.chat_id, [])` gets this tab's history (or starts an empty one). `rag.answer(q.text, conversation=history[-6:])` runs lesson 24's RAG, also sending the last 6 messages (3 questions + 3 answers) so Claude understands follow-ups. Then the new question and reply are added to the history, and the reply plus a 160-character preview of each source go back as JSON.
4. `POST /upload` (`upload(file)`): `Path(file.filename).name` keeps only the file name (so nobody can sneak in a path like `../../secret`), anything that isn't `.pdf`, `.txt` or `.md` is refused with a `400` error, the file is saved into `docs/`, and `rag.add_document(path)` chunks and stores it immediately.
5. `GET /documents` lists the unique `source` labels in the database (for the header), and `GET /` sends the web page.
6. In `page.html`, `chatId` is a random id made once per tab. `send()` shows your message, posts it to `/ask`, and replaces "Searching your documents…" with the reply and its sources. If the server returns an error, the bubble tells you to look at the terminal.

## If something goes wrong
- **`uvicorn: command not found`** (or "not recognized") → your venv is off, or uvicorn isn't installed. Switch on the venv and run the `pip install` line. You can also start it with `python -m uvicorn app:app --reload`.
- **The bubble says "⚠️ Something went wrong"** → look at the terminal. If it says `ANTHROPIC_API_KEY is not set`, stop the server (`Ctrl + C`), set the key in **that** terminal, and start it again.
- **`RuntimeError: Form data requires "python-multipart" to be installed`** → run `pip install python-multipart`.
- **`[Errno 48] Address already in use`** (or 98/10048) → another server (maybe lesson 19's) is still running on port 8000. Stop it with `Ctrl + C`, or use another port: `uvicorn app:app --reload --port 8001` and open http://127.0.0.1:8001.
- **An uploaded PDF shows `0 chunks`** → it is a scanned PDF with no real text inside. Use a PDF where you can select text with the mouse.

## Try this
1. Upload a long PDF (a manual or a book chapter) and ask about something on its **last** page. Does it find it?
   <details><summary>Hint</summary>

   It should: every page is chunked and stored, so position in the file doesn't matter. If it misses, ask using words that appear on that page.
   </details>
2. Switch the memory off: in `app.py`, change `conversation=history[-6:]` to `conversation=[]`. Restart, ask a question, then send `Explain your last answer in one simple sentence.` What happens, and why?
   <details><summary>Hint</summary>

   Claude now only sees the new message and the 4 sources, not the previous answer, so it can't know what "your last answer" means. It usually says it couldn't find it. That's exactly what chat memory is for. Change it back afterwards.
   </details>
3. A weakness: search only uses the **new** message. Ask `How do I get my travel expenses paid back?`, then `What is the deadline?`. The second message says nothing about expenses, so search returns the vacation policy first and misses the chunk with the 30-day rule (look at the Sources line under the answer). Fix it by searching with the previous question plus the new one.
   <details><summary>Solution</summary>

   In `rag.py`, let `answer` take an optional search text:
   ```python
   def answer(question: str, conversation: list | None = None, search_for: str | None = None) -> tuple[str, list[dict]]:
       sources = find_relevant(search_for or question)
   ```
   In `app.py`, inside `ask(q)`, before calling `rag.answer`:
   ```python
   previous = history[-2]["content"] if history else ""        # your last question
   reply, sources = rag.answer(q.text, conversation=history[-6:], search_for=previous + " " + q.text)
   ```
   Real products often go one step further and ask the AI to rewrite the follow-up into a complete question before searching.
   </details>

## Check yourself
1. What does the browser send to `/ask`, and what does it get back?
2. Why does every browser tab get its own `chat_id`?
3. Why send only `history[-6:]` instead of the whole conversation?
4. After you upload a file, why can you ask about it straight away, without restarting?

<details><summary>Answers</summary>

1. It sends `{chat_id, text}` (who is asking and the question). It gets back `{reply, sources}`: the answer and a preview of each source used.
2. So each conversation has its own memory. Without it, two people (or two tabs) would see each other's history mixed together.
3. Every message sent costs money and time, and very old messages rarely help. 3 exchanges are enough for follow-ups.
4. `upload()` calls `rag.add_document(path)` right after saving, which chunks the file and stores it in the vector database immediately.
</details>

## Learn more (optional)
- [FastAPI: receiving uploaded files](https://fastapi.tiangolo.com/tutorial/request-files/)
- Video search: [build a chat with your PDF app](https://www.youtube.com/results?search_query=chat+with+pdf+rag+app+python)

## Next
→ [26 · Production vector database: Postgres + pgvector](../26-production-vector-database-postgres)
