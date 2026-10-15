# Voice notes: record in the browser, Whisper writes it down, and you can search every note later.
# Run: uvicorn server:app --reload    then open http://localhost:8000
import io
import sqlite3
from datetime import datetime

from fastapi import FastAPI, UploadFile
from fastapi.responses import FileResponse
from faster_whisper import WhisperModel

model = WhisperModel("base", device="cpu", compute_type="int8")
db = sqlite3.connect("notes.db", check_same_thread=False)        # a database in one file
db.execute("CREATE TABLE IF NOT EXISTS notes (id INTEGER PRIMARY KEY, created TEXT, text TEXT)")
app = FastAPI()


@app.get("/")
def home():
    return FileResponse("index.html")


@app.post("/notes")
def add_note(audio: UploadFile):                                 # a normal "def": FastAPI runs it in a helper thread,
    sound = io.BytesIO(audio.file.read())                       # so the server stays responsive while Whisper works
    segments, _ = model.transcribe(sound, vad_filter=True)      # the browser's recording (webm) -> text
    text = " ".join(s.text.strip() for s in segments) or "(nothing heard)"
    created = datetime.now().strftime("%Y-%m-%d %H:%M")
    db.execute("INSERT INTO notes (created, text) VALUES (?, ?)", (created, text))
    db.commit()
    return {"created": created, "text": text}


@app.get("/notes")
def list_notes(q: str = ""):                                     # /notes?q=milk -> only notes containing "milk"
    rows = db.execute("SELECT id, created, text FROM notes WHERE text LIKE ? ORDER BY id DESC",
                      (f"%{q}%",)).fetchall()
    return [{"id": i, "created": c, "text": t} for i, c, t in rows]


@app.delete("/notes/{note_id}")
def delete_note(note_id: int):
    db.execute("DELETE FROM notes WHERE id = ?", (note_id,))
    db.commit()
    return {"deleted": note_id}
