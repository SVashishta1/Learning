# Capstone: a private meeting assistant. Upload or record a meeting ->
# timestamped transcript -> summary, decisions and action items -> ask questions about it -> export.
# Everything runs on your computer. Run: uvicorn server:app    then open http://localhost:8000
import io
import json
import sqlite3
from datetime import datetime

import httpx
from fastapi import FastAPI, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, PlainTextResponse
from faster_whisper import WhisperModel

MODEL = "llama3.2:3b"
whisper = WhisperModel("small", device="cpu", compute_type="int8")   # meetings deserve accuracy; "base" if slow
db = sqlite3.connect("meetings.db", check_same_thread=False)
db.execute("CREATE TABLE IF NOT EXISTS meetings "
           "(id INTEGER PRIMARY KEY, title TEXT, created TEXT, transcript TEXT, summary TEXT)")
app = FastAPI()


def ask_llm(prompt, json_mode=False):
    body = {"model": MODEL, "messages": [{"role": "user", "content": prompt}], "stream": False,
            "options": {"num_ctx": 16384}}     # room for long transcripts (Ollama's default is much smaller)
    if json_mode:
        body["format"] = "json"                 # forces valid JSON
    try:
        data = httpx.post("http://localhost:11434/api/chat", json=body, timeout=600).json()
    except httpx.ConnectError:
        raise HTTPException(503, "Can't reach Ollama. Start the Ollama app and try again.")
    if "error" in data:                         # e.g. the model isn't downloaded
        raise HTTPException(500, f"Ollama says: {data['error']}")
    return data["message"]["content"]


def transcribe(audio_bytes):
    """Every Whisper segment becomes one line: '[02:15] We'll launch on Friday.'"""
    segments, _ = whisper.transcribe(io.BytesIO(audio_bytes), vad_filter=True)
    return "\n".join(f"[{int(s.start // 60):02d}:{int(s.start % 60):02d}] {s.text.strip()}" for s in segments)


def summarize(transcript):
    # A long meeting doesn't fit in a small model at once: take notes on each piece, then summarize the notes.
    words = transcript.split()
    pieces = [" ".join(words[i:i + 2500]) for i in range(0, len(words), 2500)]
    if len(pieces) > 1:
        transcript = "\n\n".join(ask_llm(f"Write detailed bullet-point notes of this part of a meeting:\n\n{p}")
                                 for p in pieces)
    answer = ask_llm(
        "Read this meeting and reply with JSON only, in exactly this shape:\n"
        '{"summary": "3-5 sentences", "decisions": ["..."], '
        '"action_items": [{"who": "person or unknown", "task": "...", "due": "date or unknown"}]}\n\n'
        f"MEETING:\n{transcript}", json_mode=True)
    data = json.loads(answer)
    # Small models don't always follow the shape exactly, so tidy it up before saving
    decisions = [str(d) for d in data.get("decisions") or [] if d]
    actions = []
    for item in data.get("action_items") or []:
        if isinstance(item, dict):
            actions.append({"who": str(item.get("who", "unknown")), "task": str(item.get("task", "")),
                            "due": str(item.get("due", "unknown"))})
        elif item:
            actions.append({"who": "unknown", "task": str(item), "due": "unknown"})
    return {"summary": str(data.get("summary", "")), "decisions": decisions, "action_items": actions}


@app.get("/")
def home():
    return FileResponse("index.html")


@app.post("/meetings")
def add_meeting(audio: UploadFile, title: str = Form("Meeting")):
    try:                                        # check the "brain" is on BEFORE spending minutes transcribing
        httpx.get("http://localhost:11434", timeout=5)
    except httpx.ConnectError:
        raise HTTPException(503, "Can't reach Ollama. Start the Ollama app and try again.")
    transcript = transcribe(audio.file.read())
    if not transcript:
        raise HTTPException(400, "I couldn't hear any speech in that file.")
    summary = summarize(transcript)
    created = datetime.now().strftime("%Y-%m-%d %H:%M")
    row = db.execute("INSERT INTO meetings (title, created, transcript, summary) VALUES (?, ?, ?, ?)",
                     (title, created, transcript, json.dumps(summary)))
    db.commit()
    return get_meeting(row.lastrowid)


@app.get("/meetings")
def list_meetings():
    rows = db.execute("SELECT id, title, created FROM meetings ORDER BY id DESC").fetchall()
    return [{"id": i, "title": t, "created": c} for i, t, c in rows]


@app.get("/meetings/{meeting_id}")
def get_meeting(meeting_id: int):
    row = db.execute("SELECT id, title, created, transcript, summary FROM meetings WHERE id = ?",
                     (meeting_id,)).fetchone()
    if not row:
        raise HTTPException(404, "Meeting not found")
    return {"id": row[0], "title": row[1], "created": row[2], "transcript": row[3], **json.loads(row[4])}


@app.post("/meetings/{meeting_id}/ask")
def ask(meeting_id: int, question: str = Form()):
    meeting = get_meeting(meeting_id)
    answer = ask_llm("Answer the question using only this meeting transcript, and quote the [mm:ss] time "
                     "where it was said. If the answer isn't in the transcript, say so.\n\n"
                     f"TRANSCRIPT:\n{meeting['transcript']}\n\nQUESTION: {question}")
    return {"answer": answer}


@app.get("/meetings/{meeting_id}/markdown", response_class=PlainTextResponse)
def export(meeting_id: int):
    m = get_meeting(meeting_id)
    lines = [f"# {m['title']}", f"_{m['created']}_", "", "## Summary", m["summary"], "", "## Decisions"]
    lines += [f"- {d}" for d in m["decisions"]]
    lines += ["", "## Action items"]
    lines += [f"- [ ] **{a.get('who', '?')}**: {a.get('task', '')} (due: {a.get('due', '?')})" for a in m["action_items"]]
    lines += ["", "## Transcript", m["transcript"]]
    return "\n".join(lines)
