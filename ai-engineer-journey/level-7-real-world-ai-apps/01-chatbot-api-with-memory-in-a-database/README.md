# 7.1 · Chatbot API with memory in a database

**What you build:** a FastAPI chatbot backed by Claude. It **remembers** each conversation (saved in SQLite), supports **streaming** replies (text appears word by word), lets you set a persona, and tracks token usage, the thing that decides your bill.
**Like you're 10:** the AI has goldfish memory: it forgets everything between messages. So you keep a **diary** of the conversation and hand the whole diary back every time you talk. The diary is your database.

## Run it
```bash
cd level-7-real-world-ai-apps/01-chatbot-api-with-memory-in-a-database
pip install -r requirements.txt
export ANTHROPIC_API_KEY=sk-ant-...       # see the Level 7 README
uvicorn main:app --reload
```
In another terminal: `python chat_cli.py` and chat (it streams!). Tell it your name, then ask it later. Or use http://127.0.0.1:8000/docs:
1. `POST /chats` → `{"id": 1}` (optionally pass a custom `persona`)
2. `POST /chats/1/messages` with `{"content": "Hi, I'm Sam"}`
3. `GET /chats/1` to see the full history and tokens used

Tests (free, offline, fake LLM): `pytest -v`

## Key ideas
- **Stateless model, stateful app:** every request sends `system` (persona) + the **whole history**. Longer chats cost more tokens. `history(limit=40)` keeps it bounded. Real apps also summarise old turns.
- **System prompt = the persona/rules**, kept separate from user messages.
- **Streaming (SSE):** the user sees words after ~1 second instead of waiting for the full reply. Huge UX win.
- **Token accounting:** we store input/output tokens per message → you can show cost per user.
- **`effort: "low"`:** casual chat doesn't need deep reasoning; lower effort means faster and cheaper.
- **Testing with a fake client:** the test checks that *memory is sent* without spending money.

## Your turn
1. Add `DELETE /chats/{id}` and `GET /chats` (list with titles).
2. When a conversation passes 20 messages, ask Claude to summarise the oldest 10 and store the summary in the persona.
3. Add the login from 1.6 so each user only sees their own chats.

## Watch / read
- Anthropic docs, Messages API: https://platform.claude.com/docs/en/api/messages
- Streaming: https://platform.claude.com/docs/en/build-with-claude/streaming
- Server-Sent Events explained: https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events/Using_server-sent_events
