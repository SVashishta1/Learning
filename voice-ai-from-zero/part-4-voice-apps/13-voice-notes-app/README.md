# 13 · Voice notes app

**What it does:** a web page with one button. Speak a note, it's written down by Whisper and saved. Type in the search box to find any note by its words.

## Run it
```bash
cd part-4-voice-apps/13-voice-notes-app
uvicorn server:app --reload
```
Open http://localhost:8000, allow the microphone, record a few notes, then search.

## How it fits together
```
browser records (MediaRecorder) ──POST /notes──▶ FastAPI ──▶ faster-whisper ──▶ SQLite (notes.db)
browser search box ──GET /notes?q=──▶ SQLite "LIKE" search ──▶ list on the page
```
- `server.py`: 3 routes: add, list/search, delete.
- `index.html`: the recorder from project 03 + a list.

## Try this
1. Add a `title` column: ask Whisper for the first 5 words and use them as the title.
2. Add a "📋 copy" button to each note (`navigator.clipboard.writeText`).
3. Add `language=None` and show the detected language next to each note (`info.language`).
