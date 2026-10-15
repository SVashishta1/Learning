# A voice assistant web app: hold the button, talk, and it answers out loud. All local.
# Run: uvicorn server:app    then open http://localhost:8000     (Ollama must be running)
import base64
import io
import json
import urllib.request
from pathlib import Path

import httpx
import soundfile as sf
from fastapi import FastAPI, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from faster_whisper import WhisperModel
from kokoro_onnx import Kokoro

MODEL = "llama3.2:3b"
SYSTEM = ("You are a friendly voice assistant. Your replies are spoken aloud, "
          "so answer in 1-3 short sentences, with no lists, emojis or markdown.")
MODELS = Path(__file__).resolve().parents[2] / "models"          # shared with project 11: voice-ai-from-zero/models/
URL = "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/"

MODELS.mkdir(exist_ok=True)
for name in ["kokoro-v1.0.onnx", "voices-v1.0.bin"]:             # same files as project 11 (~340 MB, once)
    if not (MODELS / name).exists():
        print(f"Downloading {name} into {MODELS} (once, please wait)...")
        urllib.request.urlretrieve(URL + name, MODELS / (name + ".part"))
        (MODELS / (name + ".part")).rename(MODELS / name)

ears = WhisperModel("base", device="cpu", compute_type="int8")
mouth = Kokoro(str(MODELS / "kokoro-v1.0.onnx"), str(MODELS / "voices-v1.0.bin"))
app = FastAPI()


@app.get("/")
def home():
    return FileResponse("index.html")


@app.post("/talk")                     # a plain "def", so the slow AI work runs in a helper thread
def talk(audio: UploadFile, history: str = Form("[]"), voice: str = Form("af_heart")):
    # 1. Ears: speech -> text
    segments, info = ears.transcribe(io.BytesIO(audio.file.read()), vad_filter=True)
    heard = " ".join(s.text.strip() for s in segments)
    if not heard:
        return {"heard": "", "reply": "", "audio": ""}

    # 2. Brain: the browser sends the conversation so far, so the server stays simple
    messages = [{"role": "system", "content": SYSTEM}] + json.loads(history) + [{"role": "user", "content": heard}]
    try:
        response = httpx.post("http://localhost:11434/api/chat", timeout=120,
                              json={"model": MODEL, "messages": messages, "stream": False})
    except httpx.ConnectError:
        raise HTTPException(503, "Can't reach Ollama. Start the Ollama app and try again.")
    data = response.json()
    if "error" in data:                                        # e.g. the model isn't downloaded
        raise HTTPException(500, f"Ollama says: {data['error']}")
    reply = data["message"]["content"]

    # 3. Mouth: text -> a WAV file, sent back as text (base64) inside the JSON
    samples, rate = mouth.create(reply, voice=voice, speed=1.1, lang="en-us")
    wav = io.BytesIO()
    sf.write(wav, samples, rate, format="WAV")
    return {"heard": heard, "reply": reply, "audio": base64.b64encode(wav.getvalue()).decode()}
