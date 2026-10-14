# Real-time voice assistant: just talk, it starts answering in about a second, and you can interrupt it.
# Run: uvicorn server:app    then open http://localhost:8000 in Chrome or Edge (Ollama must be running)
#
# The 3 tricks that make it feel "live":
#  1. STREAM the microphone to the server over a WebSocket (an always-open connection), 32 ms at a time.
#  2. VOICE DETECTION (Silero, project 17) decides when you've finished, so no buttons.
#  3. STREAM the answer: speak the 1st sentence while the LLM is still writing the 2nd.
import asyncio
import io
import json
import re
import urllib.request
from collections import deque
from pathlib import Path

import httpx
import numpy as np
import soundfile as sf
import torch
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from faster_whisper import WhisperModel
from kokoro_onnx import Kokoro
from silero_vad import VADIterator, load_silero_vad

MODEL = "llama3.2:3b"
VOICE = "af_heart"
KOKORO = "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/"
SYSTEM = ("You are a friendly voice assistant. Your replies are spoken aloud, so answer in 1-3 short "
          "sentences, with no lists, emojis or markdown. If you're interrupted, don't repeat yourself.")

for name in ["kokoro-v1.0.onnx", "voices-v1.0.bin"]:
    if not Path(name).exists():
        urllib.request.urlretrieve(KOKORO + name, name)

ears = WhisperModel("base", device="cpu", compute_type="int8")
mouth = Kokoro("kokoro-v1.0.onnx", "voices-v1.0.bin")
app = FastAPI()


@app.get("/")
def home():
    return FileResponse("index.html")


def transcribe(audio):
    segments, _ = ears.transcribe(audio, beam_size=1, language="en")
    return " ".join(s.text.strip() for s in segments)


def to_wav(text):
    samples, rate = mouth.create(text, voice=VOICE, speed=1.1, lang="en-us")
    wav = io.BytesIO()
    sf.write(wav, samples, rate, format="WAV")
    return wav.getvalue()


async def sentences(chat):
    """Streams the LLM's answer word by word, and hands it out one full sentence at a time."""
    text = ""
    async with httpx.AsyncClient(timeout=120) as client:
        async with client.stream("POST", "http://localhost:11434/api/chat",
                                 json={"model": MODEL, "messages": chat, "stream": True}) as response:
            async for line in response.aiter_lines():
                if line:
                    text += json.loads(line)["message"]["content"]
                    *finished, text = re.split(r"(?<=[.!?])\s+", text)   # keep the unfinished part
                    for sentence in finished:
                        yield sentence
    if text.strip():
        yield text.strip()


async def answer(ws, audio, chat):
    heard = await asyncio.to_thread(transcribe, audio)       # to_thread = don't freeze the server
    if not heard:
        return
    await ws.send_json({"type": "you", "text": heard})
    chat.append({"role": "user", "content": heard})
    said = []
    try:
        async for sentence in sentences(chat):
            wav = await asyncio.to_thread(to_wav, sentence)
            await ws.send_json({"type": "bot", "text": sentence})
            await ws.send_bytes(wav)
            said.append(sentence)
    finally:                                                # also runs when you interrupt
        chat.append({"role": "assistant", "content": " ".join(said) or "..."})


@app.websocket("/ws")
async def conversation(ws: WebSocket):
    await ws.accept()
    vad = VADIterator(load_silero_vad(), sampling_rate=16000, min_silence_duration_ms=500)
    chat = [{"role": "system", "content": SYSTEM}]
    before = deque(maxlen=10)                               # last 0.3 s, so we keep your first syllable
    speech, talking, reply = [], False, None
    try:
        while True:
            chunk = np.frombuffer(await ws.receive_bytes(), dtype=np.float32).copy()   # 512 samples
            event = vad(torch.from_numpy(chunk))
            if event and "start" in event:
                talking, speech = True, list(before)
                if reply and not reply.done():
                    reply.cancel()                          # you interrupted: stop thinking...
                await ws.send_json({"type": "stop"})        # ...and tell the browser to stop talking
            if talking:
                speech.append(chunk)
            else:
                before.append(chunk)
            if event and "end" in event:
                talking = False
                reply = asyncio.create_task(answer(ws, np.concatenate(speech), chat))
    except WebSocketDisconnect:
        if reply:
            reply.cancel()
