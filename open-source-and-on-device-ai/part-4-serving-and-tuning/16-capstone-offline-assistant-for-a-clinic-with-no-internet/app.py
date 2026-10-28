"""The clinic assistant web app: a page for staff, a question API, an audit log, and optional local voice.

Run:  uvicorn app:app --port 8000          then open http://localhost:8000
"""
import io
import os
import tempfile
from functools import lru_cache
from pathlib import Path

from fastapi import FastAPI, HTTPException, UploadFile
from fastapi.responses import FileResponse, Response
from pydantic import BaseModel, Field

import audit
import clinic_rag

HERE = Path(__file__).resolve().parent
# Kokoro's voice files: KOKORO_DIR if set, else the voice course's folder (learning/voice-ai-from-zero/models).
# In Docker, /app has no such parent folders, so we fall back to /app/models.
PARENTS = HERE.parents
KOKORO_DIR = Path(os.environ.get("KOKORO_DIR", PARENTS[2] / "voice-ai-from-zero" / "models"
                                 if len(PARENTS) > 2 else HERE / "models"))
app = FastAPI(title="Offline clinic assistant")


class Question(BaseModel):
    question: str = Field(min_length=3, max_length=500)
    staff_id: str = Field(min_length=1, max_length=20, pattern=r"^[A-Za-z0-9_-]+$")   # letters, digits, - and _


class SpeakRequest(BaseModel):
    text: str = Field(min_length=1, max_length=2000)


@lru_cache(maxsize=1)
def index():
    """Load the search index once, on first use (restart the app after running ingest.py again)."""
    return clinic_rag.load_index()


@app.get("/")
def home():
    return FileResponse(HERE / "static" / "index.html")


@app.get("/api/health")
def health():
    """Is everything this app needs available on this machine?"""
    report = {"index": clinic_rag.DB.exists(), "audit_log_intact": audit.verify()[0]}
    try:
        names = clinic_rag.installed_models()
        report["ollama"] = True
        report["chat_model"] = clinic_rag.has_model(clinic_rag.CHAT_MODEL, names)
        report["embed_model"] = clinic_rag.has_model(clinic_rag.EMBED_MODEL, names)
    except Exception:                                   # Ollama down or not answering
        report.update(ollama=False, chat_model=False, embed_model=False)
    report["ok"] = all(report.values())
    return report


@app.post("/api/ask")
def ask(q: Question):
    try:
        result = clinic_rag.answer(q.question, index())
    except clinic_rag.OllamaError as error:
        audit.log({"event": "error", "staff_id": q.staff_id, "question": q.question, "error": str(error)})
        raise HTTPException(503, str(error))
    record = audit.log({"event": "answer", "staff_id": q.staff_id, "question": q.question,
                        "answer": result["answer"], "model": result["model"],
                        "sources": [f"{s['file']}#{s['heading']}" for s in result["sources"]]})
    return {**result, "audit_id": record["hash"][:12]}


# ---------- optional local voice (needs: pip install -r requirements-voice.txt) ----------
@lru_cache(maxsize=1)
def ears():
    from faster_whisper import WhisperModel                     # imported only if someone uses voice
    return WhisperModel("base", device="cpu", compute_type="int8")


@lru_cache(maxsize=1)
def mouth():
    from kokoro_onnx import Kokoro
    return Kokoro(str(KOKORO_DIR / "kokoro-v1.0.onnx"), str(KOKORO_DIR / "voices-v1.0.bin"))


@app.post("/api/transcribe")
async def transcribe(audio: UploadFile):
    try:
        model = ears()
    except Exception as error:                                  # package or model files missing
        raise HTTPException(501, f"Voice input is not set up on this machine ({error}).")
    with tempfile.NamedTemporaryFile(suffix=".webm", delete=False) as f:
        f.write(await audio.read())                            # the browser's recording (WebM/Opus)
    try:
        segments, _ = model.transcribe(f.name, language="en", vad_filter=True)
        text = " ".join(s.text.strip() for s in segments)
    finally:
        os.unlink(f.name)
    return {"text": text}


@app.post("/api/speak")
def speak(req: SpeakRequest):
    try:
        voice = mouth()
        import soundfile
    except Exception as error:
        raise HTTPException(501, f"Voice output is not set up on this machine ({error}).")
    samples, rate = voice.create(req.text, voice="af_heart", speed=1.0, lang="en-us")
    buffer = io.BytesIO()
    soundfile.write(buffer, samples, rate, format="WAV")
    return Response(buffer.getvalue(), media_type="audio/wav")
