# 7.1 · Chatbot API with memory in a database

**What you'll build:** a FastAPI chatbot backed by Claude. It **remembers** each conversation (saved in SQLite), supports **streaming** replies (text appears word by word), lets you set a persona, and tracks token usage, the thing that decides your bill.
**Like you're 10:** the AI has goldfish memory: it forgets everything between messages. So you keep a **diary** of the conversation and hand the whole diary back every time you talk. The diary is your database.
**Time:** ~2 h · **Builds on:** [6.5 Run an open LLM on your laptop](../../level-6-transformers/05-run-an-open-llm-on-your-laptop) and [1.5 To-do API with a database](../../level-1-apis/05-todo-api-with-sqlite-then-postgres) · **Needs:** an Anthropic API key (tests run without one)

## Why this matters
Almost every AI product starts as "a chat box connected to a model": support bots, tutors, internal assistants. The model itself is stateless, so the real engineering is around it: saving conversations, sending the right history, streaming the reply so it feels fast, and counting tokens so you know what each user costs you. This project is that backbone, and you'll reuse it in 7.6.

## What you'll learn
- **Stateless model, stateful app**: Claude remembers nothing; your app stores the chat and resends it every turn.
- **System prompt (persona)**: the instructions that set the bot's personality and rules, kept separate from user messages.
- **Streaming with Server-Sent Events (SSE)**: sending the reply in small pieces over one HTTP response.
- **Token accounting**: saving input/output tokens per message so you can see cost per chat.
- **Testing with a fake client**: proving the memory logic works without spending money or needing a key.

## Before you start
```bash
cd level-7-real-world-ai-apps/01-chatbot-api-with-memory-in-a-database
pip install -r requirements.txt
```
- `anthropic`: the official SDK for calling Claude.
- `fastapi`, `uvicorn[standard]`: the web API and the server that runs it (Level 1).
- `sqlalchemy`: talks to the database (SQLite by default, Postgres if you set `DATABASE_URL`).
- `httpx`: makes HTTP requests (used by `chat_cli.py` and FastAPI's test client).
- `pytest`: runs the tests.

**API key:** follow the [Level 7 README](../README.md#api-key-needed-from-here-on), then `export ANTHROPIC_API_KEY=sk-ant-...` (Windows PowerShell: `$env:ANTHROPIC_API_KEY="sk-ant-..."`). To keep costs tiny while experimenting: `export CLAUDE_MODEL=claude-haiku-5-5`. The tests need no key.

## Run it
1. From the course root: `cd level-7-real-world-ai-apps/01-chatbot-api-with-memory-in-a-database`
2. Run the tests (free, offline): `pytest -v`
3. Start the API: `uvicorn main:app --reload`. It creates `chat.db` in this folder the first time.
4. In a **second** terminal (same folder, venv active): `python chat_cli.py`. Tell it your name, then ask it later. Type `quit` to leave.
5. Or click around at http://127.0.0.1:8000/docs:
   1. `POST /chats` with `{}` → `{"id": 1}` (or pass `{"persona": "You are a pirate."}`)
   2. `POST /chats/1/messages` with `{"content": "Hi, I'm Sam"}`
   3. `GET /chats/1` to see the full history and tokens used

### What you should see
Tests:
```
test_main.py::test_memory_is_sent_back_every_turn PASSED
test_main.py::test_streaming_saves_the_full_reply PASSED
test_main.py::test_unknown_chat_404 PASSED
3 passed
```
The chat CLI (Claude's wording will differ every time):
```
Conversation 1. Type 'quit' (or press Ctrl+C) to leave.

you> Hi, I'm Sam
bot> Nice to meet you, Sam! What are you learning today?

you> What's my name? Any study tips?
bot> Your name is Sam. Three tips:
1. Study in short blocks.
2. Test yourself.
3. Sleep well.

you> quit
```
`GET /chats/1` afterwards:
```json
{"id": 1, "title": "Hi, I'm Sam",
 "messages": [{"role": "user", "content": "Hi, I'm Sam"},
              {"role": "assistant", "content": "Nice to meet you, Sam! What are you learning today?"},
              {"role": "user", "content": "What's my name? Any study tips?"},
              {"role": "assistant", "content": "Your name is Sam. Three tips:\n1. Study in short blocks.\n..."}],
 "tokens_used": 512}
```
What to look at: the bot knows your name in the second turn only because the first turn was resent. Stop the server, start it again, and `GET /chats/1` still works: the memory lives in `chat.db`, not in the server's RAM.

## How it works
```
chat_cli.py ──POST /chats/1/stream {"content": "..."}──► main.py
                                                           │ 1. save user message in chat.db
                                                           │ 2. history(): last 40 messages from chat.db
                                                           ▼
                                   Claude ◄── system=persona + messages=history
                                     │ streams text pieces
main.py ──"data: \"Your\"", "data: \" name\"", ... ──► chat_cli.py prints them as they arrive
        └─ 3. when done, save the full reply + token counts in chat.db
```

1. **`db.py`** defines two tables with SQLAlchemy: `Conversation` (id, title, persona) and `Message` (conversation_id, role, content, input/output tokens). `create_all()` makes them if they don't exist. `DATABASE_URL` defaults to `sqlite:///./chat.db`.
2. **`history(db, conversation_id, limit=40)`** loads the last 40 messages (newest first, then reversed to oldest first) and returns them as `[{"role": ..., "content": ...}]`, the exact shape Claude's API wants. If cutting at 40 left an assistant message first, it drops it, because the conversation must start with a user message. The limit keeps very long chats from getting slower and pricier forever.
3. **`llm.py`** (the same small helper in every Level 7–8 project) creates the client (`get_client()` reads `ANTHROPIC_API_KEY`), picks the model (`CLAUDE_MODEL`, default `claude-opus-5-5`) and wraps `create`, `parse` and `stream`. On the newest models it also turns on **server-side fallback**: if a safety check ever declines a request, the API retries it on another model in the same call. `text_of()` joins the text blocks of a reply and raises a clear error if the model declined.
4. **`main.py` → `POST /chats`** creates a conversation with the default persona (or yours). Pydantic's `Field(max_length=...)` rejects giant inputs with a 422.
5. **`POST /chats/{cid}/messages`** saves your message, calls `llm.create(...)` with `system=conv.persona` and `messages=history(...)`, saves the reply with its `usage` token counts, sets the title from your first message, and returns the reply. `output_config={"effort": "low"}` tells Claude that casual chat doesn't need deep thinking, which makes it faster and cheaper.
6. **`POST /chats/{cid}/stream`** does the same with `llm.stream(...)`. The inner generator `events()` yields one SSE line per text piece: `data: <piece>\n\n`. Each piece goes through `json.dumps`, so a line break inside it becomes `\n` and can't break the SSE format. After the last piece, `get_final_message()` gives the token counts, the full reply is saved, and `data: [DONE]` tells the client it's finished.
7. **`client = None` + `get_llm()`**: the Claude client is created on first use, not at import. That lets tests set `main.client = FakeClient(...)` before any request, so no key or network is needed.
8. **`chat_cli.py`** creates a chat, then for each line you type opens a streaming request and prints each `data:` piece (decoded with `json.loads`) the moment it arrives.
9. **`test_main.py`** uses `fake_llm.FakeClient`, which returns scripted replies and records every call in `fake.calls`. The key test checks that the *second* call contained `user, assistant, user`: proof that memory is being sent.

## If something goes wrong
- **`anthropic.AuthenticationError` or "Could not resolve authentication method"** → your key isn't set in *this* terminal. Run the `export ANTHROPIC_API_KEY=...` line again in the terminal where you start `uvicorn`.
- **`Can't reach the API. Start it first...`** from `chat_cli.py` → the server isn't running, or it's on another port. Start `uvicorn main:app --reload` in another terminal first.
- **`ERROR: [Errno 98] Address already in use`** → something already uses port 8000 (maybe an earlier server). Stop it with Ctrl+C, or run `uvicorn main:app --reload --port 8001` and change `BASE` in `chat_cli.py`.
- **`anthropic.NotFoundError` mentioning the model** → `CLAUDE_MODEL` has a typo. Use an exact ID such as `claude-haiku-5-5` or unset it.
- **Old conversations behave strangely after you edited `db.py`** → `create_all()` doesn't change existing tables. Delete `chat.db` (you lose saved chats) and restart.

## Try this
1. **List and delete chats.** Add `GET /chats` (id + title of every chat) and `DELETE /chats/{cid}`.
   <details><summary>Solution</summary>

   ```python
   @app.get("/chats")
   def list_chats():
       with Session() as db:
           return [{"id": c.id, "title": c.title} for c in db.query(Conversation).order_by(Conversation.id)]


   @app.delete("/chats/{cid}", status_code=204)
   def delete_chat(cid: int):
       with Session() as db:
           conv = _load(db, cid)                                      # 404 if it doesn't exist
           db.query(Message).filter_by(conversation_id=cid).delete()  # delete the messages first
           db.delete(conv)
           db.commit()
   ```
   </details>
2. **Show the cost.** Add `"cost_usd"` to `GET /chats/{cid}`. Prices are per million tokens: Claude Haiku 5.5 is $0.10 input / $0.50 output; Claude Opus 5.5 is $4 / $20.
   <details><summary>Hint</summary>

   Sum `input_tokens` and `output_tokens` separately, then `cost = inp / 1e6 * 4.00 + out / 1e6 * 20.00` (Opus 5.5 prices). Notice how input tokens grow every turn, because the whole history is resent. That's the hidden cost of chat memory.
   </details>
3. **Summarise old turns.** When a conversation passes 20 messages, ask Claude to summarise everything except the last 10, and send that summary instead of the old messages.
   <details><summary>Hint</summary>

   In `send()`, after loading `msgs = history(db, cid, limit=1000)`: if `len(msgs) > 20`, call `llm.create(get_llm(), max_tokens=500, messages=msgs[:-10] + [{"role": "user", "content": "Summarise our conversation so far in 5 bullet points."}])`, then pass `system=conv.persona + "\n\nEarlier in this chat: " + summary` and `messages=msgs[-10:]` to the real call. Make sure `msgs[-10:]` starts with a user message (drop the first item if it doesn't). Store the summary on the conversation so you don't recompute it every turn.
   </details>

## Check yourself
1. If you restart the server, why does the bot still remember your name?
2. Why do input tokens per request keep growing during a long chat?
3. What problem does streaming solve? Does it make the full answer arrive sooner?
4. Why do the tests use `FakeClient` instead of calling Claude?

<details><summary>Answers</summary>

1. The conversation is stored in `chat.db`. Each request loads the history from the database and sends it to Claude, so nothing depends on the server's memory.
2. Every request resends the whole history (up to 40 messages), so each turn includes all earlier turns as input.
3. It solves *perceived* waiting: the first words appear after about a second instead of after the whole reply is done. The full answer takes about the same total time.
4. Tests must be free, fast, offline and deterministic (same result every run). A real model costs money, needs a key and gives different wording each time, which would make tests flaky.
</details>

## Learn more (optional)
- Anthropic docs, Messages API: https://platform.claude.com/docs/en/api/messages
- Streaming: https://platform.claude.com/docs/en/build-with-claude/streaming
- Server-Sent Events explained (MDN): https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events/Using_server-sent_events

## Next
→ [7.2 · Structured data extractor: invoices → validated JSON](../02-structured-data-extractor-invoices-to-json)
