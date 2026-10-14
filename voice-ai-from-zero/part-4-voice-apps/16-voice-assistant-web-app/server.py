# A voice assistant web app: hold the button, talk, and it answers out loud. All local.
# Run: uvicorn server:app    then open http://localhost:8000     (Ollama must be running)
import base64
import io
import json
import urllib.request
from pathlib import Path

import httpx
import soundfile as sf
from fastapi import FastAPI, Form, UploadFile
from fastapi.responses import FileResponse
from faster_whisper import WhisperModel
from kokoro_onnx import Kokoro

MODEL = "llama3.2:3b"
KOKORO = "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/"
SYSTEM = ("You are a friendly voice assistant. Your replies are spoken aloud, "
          "so answer in 1-3 short sentences, with no lists, emojis or markdown.")

for name in ["kokoro-v1.0.onnx", "voices-v1.0.bin"]:
    if not Path(name).exists():
        urllib.request.urlretrieve(KOKORO + name, name)

ears = WhisperModel("base", device="cpu", compute_type="int8")
mouth = Kokoro("kokoro-v1.0.onnx", "voices-v1.0.bin")
app = FastAPI()


@app.get("/")
def home():
    return FileResponse("index.html")


@app.post("/talk")
async def talk(audio: UploadFile, history: str = Form("[]"), voice: str = Form("af_heart")):
    # 1. Ears: speech -> text
    segments, info = ears.transcribe(io.BytesIO(await audio.read()), vad_filter=True)
    heard = " ".join(s.text.strip() for s in segments)
    if not heard:
        return {"heard": "", "reply": "", "audio": ""}

    # 2. Brain: the browser sends the conversation so far, so the server stays simple
    messages = [{"role": "system", "content": SYSTEM}] + json.loads(history) + [{"role": "user", "content": heard}]
    async with httpx.AsyncClient(timeout=120) as client:
        response = await client.post("http://localhost:11434/api/chat",
                                     json={"model": MODEL, "messages": messages, "stream": False})
    reply = response.json()["message"]["content"]

    # 3. Mouth: text -> a WAV file, sent back as text (base64) inside the JSON
    samples, rate = mouth.create(reply, voice=voice, speed=1.1, lang="en-us")
    wav = io.BytesIO()
    sf.write(wav, samples, rate, format="WAV")
    return {"heard": heard, "reply": reply, "audio": base64.b64encode(wav.getvalue()).decode()}
