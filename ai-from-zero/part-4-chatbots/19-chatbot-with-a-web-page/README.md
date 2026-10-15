# 19 · Chatbot with a web page

**What you'll build:** your own mini ChatGPT: a chat page in your browser, replies that appear word by word, conversations saved in a database, and a "New chat" button.
**Time:** ~1 hour · **Builds on:** [18 · Chatbot API that saves chats](../18-chatbot-api-that-saves-chats) · **Needs:** an Anthropic API key (see the [Part 4 README](../README.md))

## Why this matters
This is the full shape of a real chat product: a front end (the page), a back end (your API), a database, and a model, with replies **streamed** so users aren't staring at a blank screen. Once you've built it, apps like ChatGPT and Claude.ai stop being magic: they're this, plus polish.

## What you'll learn
- **Front end and back end:** `page.html` runs in the browser; `app.py` runs on your computer and talks to Claude.
- **Streaming over HTTP:** the API sends the reply in small pieces as Claude writes them, and the page adds each piece as it arrives.
- **Browser storage:** the page remembers which chat you're in using `localStorage`, so refreshing doesn't lose your conversation.
- **Loading history:** when the page opens, it asks the API for the saved messages and redraws them.

## Before you start
- Install (with your virtual environment on):
  ```bash
  pip install anthropic fastapi "uvicorn[standard]" pydantic
  ```
  `anthropic` talks to Claude, `fastapi` + `uvicorn` run the API and serve the page, `pydantic` checks incoming data.
- **API key:** `ANTHROPIC_API_KEY` must be set in the terminal where you start the server (see **Get your API key** in the [Part 4 README](../README.md)).
- Files here: `app.py` (the API), `page.html` (the chat page), `ai.py` (the helper from project 17).

## Run it
1. Open a terminal in the `ai-from-zero` folder.
2. Start the server:
   ```bash
   cd part-4-chatbots/19-chatbot-with-a-web-page
   uvicorn app:app --reload
   ```
3. Open http://127.0.0.1:8000 and chat.
4. Refresh the page: your conversation is still there. Click **New chat** to start a fresh one.
5. Stop the server with `Ctrl + C` when you're done.

### What you should see
In the terminal:
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Application startup complete.
INFO:     127.0.0.1:50420 - "GET / HTTP/1.1" 200 OK
INFO:     127.0.0.1:50420 - "GET /history/k3j9x2a7q HTTP/1.1" 200 OK
INFO:     127.0.0.1:50420 - "POST /chat HTTP/1.1" 200 OK
```
In the browser: a dark header "🤖 My Chatbot", your messages in blue bubbles on the right, and the bot's replies on the left, appearing word by word (Claude's wording will vary):
```
                                   [ Hi! I'm Priya. Can you help me plan a picnic? ]
[ Hi Priya! I'd love to help. 🧺                    ]
[ How many people are coming, and is it a park      ]
[ or a beach picnic?                                ]
```
The random letters after `/history/` are your chat's ID. A `chats.db` file appears in this folder.

## How it works
```
 page.html (browser)                         app.py (your computer)                 Claude
 type + Send ──POST /chat {chat_id, text}──→ save your message in chats.db
                                             load the whole chat ──ai.stream()──→ writes reply
 add each piece to ←── piece, piece, piece ── pass each piece on      ←── piece by piece
 the bot bubble                              when done: save the full reply in chats.db
```
**app.py**
1. **Startup.** `ai.client()` checks your API key (stops with a ❌ message if missing). It opens `chats.db` and makes the `messages` table. Here `chat_id` is text, because the browser invents the IDs.
2. **`POST /chat`** rejects empty text (`400`), saves your message, and loads the whole chat (`history`).
3. **`live_reply()`** is a **generator**: a function that `yield`s pieces one at a time. For each piece from `ai.stream(...)` it adds it to `reply` and yields it. When the stream ends, it saves the complete reply in the database.
4. **`StreamingResponse(live_reply(), ...)`** sends each yielded piece to the browser the moment it's ready, instead of waiting for the whole reply.
5. **`GET /history/{chat_id}`** returns the saved messages of one chat. **`GET /`** sends `page.html`.

**page.html**
1. **Chat ID.** `localStorage.getItem("chatId")` reads the ID saved in your browser; if there isn't one, `newId()` makes a random one and saves it. That's how a refresh returns to the same chat.
2. **`bubble(cls, text)`** adds one message bubble to the page and scrolls down.
3. **`send()`** runs when you press Send: it shows your bubble and an empty bot bubble (`…`), then `fetch("/chat", ...)` posts your message. If the server answers with an error, the bubble shows a ⚠️ message.
4. **Reading the stream.** `r.body.getReader()` reads the reply as it arrives; each chunk is turned from bytes into text with `TextDecoder` (`{stream: true}` keeps emoji and accented letters intact when they're split between chunks) and added to the bot bubble.
5. **On page load**, `fetch("/history/" + chatId)` redraws the saved conversation. **New chat** makes a new ID and clears the screen (the old chat stays in the database).

## If something goes wrong
- **Server stops at once with `❌ ANTHROPIC_API_KEY is not set in this terminal`** → set the key in the terminal you start uvicorn from, then start it again.
- **The bot bubble says "⚠️ No reply" or "⚠️ Something went wrong"** → look at the terminal running uvicorn; the last lines say what went wrong (wrong key, no credit, no internet). Fix it, restart uvicorn if it stopped, and send again.
- **Blank page or `RuntimeError: File at path page.html does not exist`** → you started uvicorn from the wrong folder. `cd part-4-chatbots/19-chatbot-with-a-web-page` first.
- **`[Errno 48] Address already in use`** (or `[Errno 98]`, or `10048` on Windows) → another server (maybe project 18) is still running. Stop it, or use `--port 8001` and open http://127.0.0.1:8001.
- **Old messages keep coming back** → that's the saved chat. Click **New chat**, or delete `chats.db` (with the server stopped) to wipe everything.

## Try this
1. **New personality.** Change `PERSONALITY` in `app.py` to make it a cooking assistant or a language tutor (for example `"You are a patient Spanish tutor. Reply in simple Spanish, then give the English translation in brackets."`). Save, then click **New chat**.
   <details><summary>Hint</summary>

   With `--reload` the server restarts itself when you save. Only the system prompt changed, yet it's a completely different product.
   </details>
2. **Make it yours.** Change the colours in `page.html`. Look for `#2563eb` (the blue of your messages) and `#16202a` (the dark header). Change the title text "🤖 My Chatbot" too.
   <details><summary>Hint</summary>

   Colours are written as `#` plus 6 hex digits (red, green, blue). Search "color picker" in your browser to find codes, for example `#16a34a` for green. Save the file and refresh the page; no server restart needed for HTML changes.
   </details>
3. **Chat from your phone.** Start the server with `uvicorn app:app --host 0.0.0.0` and open `http://<your-computer's-IP>:8000` on your phone (same Wi-Fi).
   <details><summary>Hint</summary>

   Find your computer's IP: Windows `ipconfig` (IPv4 Address), Mac `ipconfig getifaddr en0`, Linux `hostname -I`. If the phone can't connect, allow Python through your firewall when your computer asks. Your phone gets its own chat ID, because `localStorage` belongs to each browser. Only do this on a network you trust: anyone on it could use your chatbot (and your credit).
   </details>

## Check yourself
1. What runs in the browser, and what runs on your computer's server?
2. Why does the reply appear word by word, and what two pieces of code make that happen?
3. How does the page know which conversation to show after a refresh?
4. Why must the API key stay in `app.py`'s terminal and never go into `page.html`?

<details><summary>Answers</summary>

1. `page.html` (the page and its JavaScript) runs in the browser. `app.py`, the database and the calls to Claude run on your computer.
2. Streaming: `ai.stream()` + `StreamingResponse` send pieces as Claude writes them, and the page's `getReader()` loop adds each piece to the bubble as it arrives.
3. The chat ID is saved in the browser's `localStorage`; on load the page asks `/history/<that ID>` for the saved messages.
4. Anything in a web page can be seen by whoever opens it (View Source). The key must stay on the server, which calls Claude on the page's behalf.
</details>

## Learn more (optional)
- Streaming replies from Claude (official docs): https://platform.claude.com/docs/en/build-with-claude/streaming
- FastAPI custom responses, including `StreamingResponse`: https://fastapi.tiangolo.com/advanced/custom-response/
- Search: "JavaScript fetch API explained" https://www.youtube.com/results?search_query=javascript+fetch+api+explained

## Next
→ [20 · AI turns messy text into data](../20-ai-turns-messy-text-into-data)
