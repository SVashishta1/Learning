# 18 · Chatbot API that saves chats

**What you'll build:** your chatbot behind an API (Part 1 skills!). Each conversation gets a number, and every message is saved in a database, so chats survive restarts and many people can each have their own.
**Time:** ~1 hour · **Builds on:** [17 · Chatbot with memory](../17-chatbot-with-memory) and [03 · API that saves to a database](../../part-1-apis/03-api-that-saves-to-a-database) · **Needs:** an Anthropic API key (see the [Part 4 README](../README.md))

## Why this matters
A chatbot in your terminal works for one person until you close it. Real products (a support bot on a website, a chat feature inside an app) run as an API: any app or web page can start a chat, send messages, and read the history, and nothing is lost when the server restarts. This "AI behind an API with a database" shape is one of the most common things AI engineers build.

## What you'll learn
- **Persistent memory:** storing the conversation in a database table instead of a Python list.
- **Chat IDs:** giving each conversation its own number so users don't see each other's chats.
- **Endpoints for a chatbot:** create a chat, send a message, read the history.
- **HTTP error codes:** `404` for "no such chat", `400` for a bad request, `500` when something broke on the server.

## Before you start
- Install (with your virtual environment on):
  ```bash
  pip install anthropic fastapi "uvicorn[standard]" pydantic
  ```
  `anthropic` talks to Claude, `fastapi` + `uvicorn` run your API, `pydantic` checks the shape of incoming data. The database is SQLite, which is built into Python.
- **API key:** `ANTHROPIC_API_KEY` must be set in the terminal where you start the server (see **Get your API key** in the [Part 4 README](../README.md)).
- This folder has `main.py` (the API) and `ai.py` (the helper from project 17).

## Run it
1. Open a terminal in the `ai-from-zero` folder.
2. Start the server:
   ```bash
   cd part-4-chatbots/18-chatbot-api-that-saves-chats
   uvicorn main:app --reload
   ```
3. Open http://127.0.0.1:8000/docs. For each step, click the endpoint, then **Try it out**, fill in the box, then **Execute**:
   1. **POST /chats** → you get `{"chat_id": 1}`
   2. **POST /chats/{chat_id}** with `chat_id` = `1` and the body `{"text": "Hi, I'm Sam and I love football"}`
   3. **POST /chats/{chat_id}** with `chat_id` = `1` and `{"text": "What do I love?"}` → it remembers
   4. **GET /chats/{chat_id}** with `chat_id` = `1` → the whole saved conversation
4. Stop the server (`Ctrl + C`), start it again, and send another message to chat 1. It still remembers.

### What you should see
The terminal shows the server starting, then one line per request:
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Application startup complete.
INFO:     127.0.0.1:50312 - "POST /chats HTTP/1.1" 200 OK
INFO:     127.0.0.1:50312 - "POST /chats/1 HTTP/1.1" 200 OK
```
The responses in `/docs` look like this (Claude's wording will differ):
```
POST /chats            → {"chat_id": 1}
POST /chats/1          → {"reply": "Hi Sam! Football is brilliant. Do you play, or support a team?"}
POST /chats/1          → {"reply": "You love football! ⚽"}
GET  /chats/1          → [{"role": "user", "content": "Hi, I'm Sam and I love football"},
                          {"role": "assistant", "content": "Hi Sam! Football is brilliant. ..."},
                          {"role": "user", "content": "What do I love?"},
                          {"role": "assistant", "content": "You love football! ⚽"}]
```
A file called `chats.db` appears in this folder. That's the database.

## How it works
```
 app or /docs ──POST /chats/1 {"text": ...}──→ main.py
                                               1. save your message in chats.db
                                               2. load ALL of chat 1 from chats.db
                                               3. ai.ask(whole chat) ──→ Claude
                                               4. save Claude's reply in chats.db
 app or /docs ←──────── {"reply": ...} ────────5. send the reply back
```
1. **Startup.** `ai.client()` checks your API key straight away, so a missing key stops the server with a clear ❌ message. `sqlite3.connect("chats.db", ...)` opens the database file (creating it the first time). Two tables are made if they don't exist yet:
   - `chats`: one row per chat; its `id` is the chat number.
   - `messages`: every message ever sent, with its `chat_id`, `role` (`user` or `assistant`) and `content`.
2. **`PERSONALITY`** is the system prompt for every chat.
3. **`Message`** says the request body must be JSON like `{"text": "..."}`.
4. **Helper functions.** `chat_exists()` checks a chat number is real. `load_chat()` reads one chat's messages in order and turns them into the same list of `{"role", "content"}` dictionaries as project 17. `save()` adds one message and commits (really writes it to the file).
5. **`POST /chats`** inserts a new row in `chats`; the database picks the next number (`lastrowid`) and you get it back.
6. **`POST /chats/{chat_id}`** answers `404` if the chat doesn't exist and `400` if the text is empty. Otherwise it saves your message, loads the **whole** chat, sends it to Claude with `ai.ask(...)`, saves the reply and returns it. Same memory trick as project 17, but the list now lives in the database.
7. **`GET /chats/{chat_id}`** returns the saved conversation.

## If something goes wrong
- **Server stops at once with `❌ ANTHROPIC_API_KEY is not set in this terminal`** → set the key in the terminal you start uvicorn from, then start it again.
- **`404 Not Found` with `"No such chat. Create one first with POST /chats"`** → run **POST /chats** first and use the number it gives you.
- **`422 Unprocessable Entity`** → the body isn't in the right shape. It must be exactly `{"text": "your message"}` with double quotes.
- **`500 Internal Server Error`** → look at the terminal running uvicorn: the last lines say what went wrong (often a wrong key, no credit, or no internet).
- **`[Errno 48] Address already in use`** (or `[Errno 98]`, or `10048` on Windows) → another server is running. Stop it with `Ctrl + C`, or add `--port 8001` and use http://127.0.0.1:8001/docs.

To start completely fresh, stop the server and delete `chats.db`.

## Try this
1. **Chats are private.** Create chat 2 with **POST /chats** and ask it "What do I love?". Does it know about chat 1?
   <details><summary>Hint</summary>

   No. `load_chat(2)` only loads rows where `chat_id = 2`, so Claude never sees chat 1. This is how one server keeps thousands of users' chats apart.
   </details>
2. **Change the job.** Set `PERSONALITY` to make it the support agent for a pizza shop, for example `"You are the friendly assistant for Pizza Palace. Menu: Margherita £8, Pepperoni £10, Veggie £9. Only talk about our pizzas and orders. Keep answers under 60 words."` Save (with `--reload` the server restarts by itself) and start a new chat.
   <details><summary>Hint</summary>

   Ask about the menu, then ask about something unrelated (like homework). A clear system prompt keeps a business bot on topic. New chats use the new personality; old messages stay as they were.
   </details>
3. **List all chats.** Add a `GET /chats` endpoint that returns every chat number with how many messages it has.
   <details><summary>Solution</summary>

   Add this at the bottom of `main.py`:
   ```python
   @app.get("/chats")
   def list_chats():
       rows = db.execute("SELECT chats.id, COUNT(messages.id) FROM chats "
                         "LEFT JOIN messages ON messages.chat_id = chats.id GROUP BY chats.id").fetchall()
       return [{"chat_id": chat_id, "messages": count} for chat_id, count in rows]
   ```
   It returns something like `[{"chat_id": 1, "messages": 4}, {"chat_id": 2, "messages": 0}]`. `LEFT JOIN` keeps chats that have no messages yet; `COUNT` and `GROUP BY` count the messages per chat.
   </details>

## Check yourself
1. Why does the chat survive a server restart now, when the project 17 chatbot forgot everything?
2. When you send the 5th message in a chat, what exactly does the server send to Claude?
3. Why does each chat need its own number?
4. Why does the server check the API key as soon as it starts?

<details><summary>Answers</summary>

1. The messages are stored in the `chats.db` file, not in a Python list in memory, and files stay on disk when a program stops.
2. All 5 of your messages and the 4 earlier replies from that chat (loaded from the database), plus the system prompt.
3. So the server can load just one conversation at a time and keep different users' chats apart.
4. So you find out about a missing key immediately, with a clear message, instead of getting a confusing error on the first chat message.
</details>

## Learn more (optional)
- FastAPI path parameters and request bodies: https://fastapi.tiangolo.com/tutorial/body/
- SQLite in Python (official docs): https://docs.python.org/3/library/sqlite3.html

## Next
→ [19 · Chatbot with a web page](../19-chatbot-with-a-web-page)
