# Talk to an AI out loud, 100% on your computer:
#   your voice -> Whisper (ears) -> Llama via Ollama (brain) -> Kokoro (mouth) -> your speakers
# Needs Ollama running with: ollama pull llama3.2:3b
import sys
import urllib.request
from pathlib import Path

import httpx
import numpy as np
import sounddevice as sd
from faster_whisper import WhisperModel
from kokoro_onnx import Kokoro

MODEL = "llama3.2:3b"
VOICE = "af_heart"
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
chat = [{"role": "system", "content": "You are a friendly voice assistant. Your replies are spoken aloud, "
                                      "so answer in 1-3 short sentences, with no lists, emojis or markdown."}]


def record():
    """Records from Enter to Enter."""
    chunks = []
    input("\nPress Enter, then speak...")
    with sd.InputStream(samplerate=16000, channels=1, dtype="float32",
                        callback=lambda chunk, *_: chunks.append(chunk[:, 0].copy())):
        input("🔴 Recording. Press Enter when you're done.")
    return np.concatenate(chunks) if chunks else np.zeros(0, dtype=np.float32)


def think(text):
    chat.append({"role": "user", "content": text})
    try:
        response = httpx.post("http://localhost:11434/api/chat", timeout=120,
                              json={"model": MODEL, "messages": chat, "stream": False})
    except httpx.ConnectError:
        sys.exit("Can't reach Ollama. Start the Ollama app (or run 'ollama serve') and try again.")
    data = response.json()
    if "error" in data:                                       # e.g. "model 'llama3.2:3b' not found"
        sys.exit(f"Ollama says: {data['error']}. Did you run 'ollama pull {MODEL}'?")
    reply = data["message"]["content"]
    chat.append({"role": "assistant", "content": reply})     # remember the conversation
    return reply


def speak(text):
    samples, rate = mouth.create(text, voice=VOICE, speed=1.1, lang="en-us")
    sd.play(samples, rate)
    sd.wait()


print("🗣️  Say 'goodbye' to finish.")
while True:
    audio = record()
    if len(audio) < 16000 // 2:                               # less than half a second
        print("(That was too short. Try again.)")
        continue
    segments, _ = ears.transcribe(audio, vad_filter=True)
    heard = " ".join(s.text.strip() for s in segments)
    if not heard:
        print("(I didn't catch that)")
        continue
    print("🧑", heard)
    reply = think(heard)
    print("🤖", reply)
    speak(reply)
    if "goodbye" in heard.lower():
        break
