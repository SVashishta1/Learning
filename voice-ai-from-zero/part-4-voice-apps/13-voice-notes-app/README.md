# 13 · Voice notes app

**What you'll build:** a small web app with one big button. Speak a note, Whisper writes it down, and it's saved in a database. Type in the search box to find any note by its words; click ✕ to delete one.
**Like you're 10:** a notebook that listens. You talk, it writes, and it can find any page for you later.
**Time:** ~2 h · **Builds on:** [12 · Speech in the browser](../../part-3-text-to-speech/12-speech-in-the-browser), the recorder from [03](../../part-1-sound-basics/03-voice-recorder-in-the-browser) and faster-whisper from [05](../../part-2-speech-to-text/05-faster-whisper-live-microphone) · **Needs:** a microphone, a browser

## Why this matters
This is the shape of most real voice products: a **front end** (the web page) records, a **back end** (a Python server) runs the AI, and a **database** keeps the results. Voice memo apps, doctors' dictation tools and customer-call archives all work like this. Once you can build it, you can build many variations.

## What you'll learn
- **Client and server**: the browser page (client) sends requests; `server.py` (server) answers them.
- **API routes**: URLs the server answers, like `POST /notes` (add), `GET /notes` (list/search), `DELETE /notes/3` (delete).
- **FastAPI + uvicorn**: FastAPI is the Python library that defines the routes; uvicorn is the program that runs it as a web server.
- **SQLite**: a full database stored in one file (`notes.db`), built into Python.
- **File upload (`FormData` / `UploadFile`)**: how the recording travels from the browser to Python.

## Before you start
Activate your venv and install the Part 4 packages (one line for all of Part 4):
```bash
pip install faster-whisper "av<19" kokoro-onnx fastapi uvicorn python-multipart httpx pyttsx3 sounddevice soundfile numpy
```
- `faster-whisper` + `"av<19"`: speech to text; `av` decodes the browser's `.webm` recording.
- `fastapi`, `uvicorn`, `python-multipart`: the web server, the program that runs it, and the part that reads uploaded files.
- The others (`kokoro-onnx`, `httpx`, `pyttsx3`, `sounddevice`, `soundfile`, `numpy`) are for projects 14–16.

No API key needed. The first start downloads Whisper `base` (~145 MB) if you haven't already.

## Run it
1. From the course folder:
   ```bash
   cd part-4-voice-apps/13-voice-notes-app
   uvicorn server:app --reload
   ```
   `server:app` means "the `app` object inside `server.py`". `--reload` restarts the server when you edit the code.
2. Wait for `Application startup complete`, then open http://localhost:8000.
3. Click **Start recording**, allow the microphone, say a note ("Buy milk and call the dentist on Monday"), click **Stop**.
4. Record two or three more notes, then type a word in the search box.
5. Stop the server with `Ctrl+C`.

### What you should see
In the terminal (each line is one request from the page):
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Application startup complete.
INFO:     127.0.0.1:33974 - "GET / HTTP/1.1" 200 OK
INFO:     127.0.0.1:33974 - "GET /notes?q= HTTP/1.1" 200 OK
INFO:     127.0.0.1:33984 - "POST /notes HTTP/1.1" 200 OK
INFO:     127.0.0.1:33984 - "GET /notes?q=fox HTTP/1.1" 200 OK
INFO:     127.0.0.1:33984 - "DELETE /notes/1 HTTP/1.1" 200 OK
```
On the page, after "✍️ writing it down..." a note card appears:
```
2026-10-15 04:12                                                     ✕
The quick brown fox jumps over the lazy dog. Machine learning is fun.
```
Searching `fox` keeps it; searching `zebra` shows nothing. A new file, `notes.db`, appears in the folder: that's your database. Restart the server and your notes are still there.

## How it works
```
browser records (MediaRecorder) ──POST /notes──▶ FastAPI ──▶ faster-whisper ──▶ SQLite (notes.db)
browser search box ──GET /notes?q=──▶ SQLite "LIKE" search ──▶ list on the page
✕ button ──DELETE /notes/{id}──▶ SQLite delete
```

**`server.py`**
1. **Start-up** (runs once): loads `WhisperModel("base", ...)`, opens `notes.db` with `sqlite3.connect(...)` (creating it if needed), and makes the `notes` table if it doesn't exist: columns `id` (a number that counts up by itself), `created` and `text`. `check_same_thread=False` lets the helper threads FastAPI uses share the connection.
2. **`@app.get("/")`** returns `index.html`. The `@app.get(...)` line above a function is a **decorator**: it tells FastAPI "call this function for this URL".
3. **`@app.post("/notes")` → `add_note(audio: UploadFile)`**: FastAPI sees the type `UploadFile` and hands over the uploaded file. `io.BytesIO(...)` wraps the bytes so Whisper can read them like a file. `model.transcribe(...)` turns them into text; empty results become `"(nothing heard)"`. Then an `INSERT` saves it and `db.commit()` makes it permanent. It's a normal `def` (not `async def`) on purpose: FastAPI runs it in a helper thread, so the server keeps answering other requests while Whisper works.
4. **`@app.get("/notes")` → `list_notes(q="")`**: `/notes?q=milk` puts `"milk"` into `q`. The SQL `WHERE text LIKE ?` with `%milk%` means "contains milk" (any letters before or after). The `?` is filled in by sqlite safely, which prevents **SQL injection** (someone typing SQL commands into the search box). The result is turned into a list of dictionaries, which FastAPI sends as JSON.
5. **`@app.delete("/notes/{note_id}")`**: `{note_id}` in the URL becomes the `note_id` argument (FastAPI converts it to `int`).

**`index.html`**
6. The **record button** reuses project 03's code. When you stop, `onstop` puts the recording in a `FormData` (like a form with a file attached) under the name `audio`, the same name as the `audio` argument in `add_note`, and `fetch("/notes", { method: "POST", body: form })` sends it.
7. **`loadNotes()`** asks `GET /notes?q=...` and draws a card for each note. It uses `textContent` for the note text, so if a note contains HTML it's shown as text, never run as code.
8. **Search** calls `loadNotes()` on every key press (`oninput`). The ✕ link sends `DELETE` and reloads the list.

## If something goes wrong
- **`Error loading ASGI app. Could not import module "server"`** → you're not in the project folder. `cd part-4-voice-apps/13-voice-notes-app` first.
- **`RuntimeError: Form data requires "python-multipart" to be installed`** → `pip install python-multipart`.
- **`[Errno 98]` / `[WinError 10048]` address already in use** → another server uses port 8000 (maybe another project). Stop it, or run `uvicorn server:app --reload --port 8001` and open http://localhost:8001.
- **The note says "(nothing heard)"** → the recording was silent: check the microphone permission (🔒 icon in the address bar) and speak for at least 2 seconds.
- **"❌ Something went wrong"** → read the error in the terminal. An error about `av` means you need `pip install "av<19"`.

## Try this
1. **Easy:** add a "📋 copy" button to each note that copies its text.
   <details><summary>Hint</summary>In <code>loadNotes()</code>, change the card HTML to include <code>&lt;button class="copy"&gt;📋&lt;/button&gt;</code>, then add:<br><code>div.querySelector(".copy").onclick = () => navigator.clipboard.writeText(n.text);</code></details>
2. **Medium:** show how many notes match the search, e.g. "3 notes".
   <details><summary>Hint</summary>Add <code>&lt;p id="count"&gt;&lt;/p&gt;</code> above the notes, and at the end of <code>loadNotes()</code>: <code>document.getElementById("count").textContent = notes.length + " notes";</code>. The data is already there; you only need to show it.</details>
3. **Harder:** detect each note's language and show it next to the date (e.g. `en`, `es`).
   <details><summary>Solution</summary>

   In `server.py`:
   - change the table line to `"CREATE TABLE IF NOT EXISTS notes (id INTEGER PRIMARY KEY, created TEXT, text TEXT, lang TEXT)"` and **delete the old `notes.db`** (the old table has no `lang` column);
   - in `add_note`: `segments, info = model.transcribe(sound, vad_filter=True)` and insert `info.language` too: `"INSERT INTO notes (created, text, lang) VALUES (?, ?, ?)", (created, text, info.language)`;
   - in `list_notes`: `SELECT id, created, text, lang ...` and return `{"id": i, "created": c, "text": t, "lang": l} for i, c, t, l in rows`.

   In `index.html`, show it: `<small>${n.created} · ${n.lang}</small>`.
   </details>

## Check yourself
1. Which part runs Whisper: the browser or the server? Which part keeps the notes?
2. What does `WHERE text LIKE ?` with `%milk%` find?
3. Why is `add_note` a plain `def` rather than `async def`?
4. Why does `loadNotes()` use `textContent` for the note text?

<details><summary>Answers</summary>

1. The server (`server.py`) runs Whisper and keeps the notes in `notes.db`. The browser only records, sends and displays.
2. Every note whose text contains "milk" anywhere (case-insensitive for English letters).
3. Transcribing is slow, blocking work. FastAPI runs plain `def` routes in a helper thread, so the server can still answer other requests meanwhile.
4. So text is always shown as text. With `innerHTML`, a note containing `<script>` or `<img onerror=...>` could run code in the page.
</details>

## Learn more (optional)
- FastAPI tutorial (first steps, path and query parameters, request files): https://fastapi.tiangolo.com/tutorial/
- SQLite in Python: https://docs.python.org/3/library/sqlite3.html
- Search YouTube for "FastAPI crash course".

## Next
→ [14 · Voice commands](../14-voice-commands)
