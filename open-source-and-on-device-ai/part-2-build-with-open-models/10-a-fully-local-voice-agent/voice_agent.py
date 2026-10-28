"""A hands-free voice agent, 100% on your computer:
   microphone -> Silero VAD (is someone talking?) -> faster-whisper (ears)
   -> agent.py: Llama via Ollama + tools (brain) -> Kokoro (mouth) -> speakers

Run:  python voice_agent.py          (use headphones!)
"""
import queue
import urllib.request
from collections import deque
from pathlib import Path

import numpy as np
import sounddevice as sd
import torch
from faster_whisper import WhisperModel
from kokoro_onnx import Kokoro
from silero_vad import VADIterator, load_silero_vad

from agent import MODEL, ask, timer_alerts

RATE, CHUNK = 16000, 512                  # Silero listens to 512 samples (32 ms) at a time
VOICE = "af_heart"
# Reuse Kokoro's files from the voice course: learning/voice-ai-from-zero/models/
MODELS = Path(__file__).resolve().parents[3] / "voice-ai-from-zero" / "models"
URL = "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/"

MODELS.mkdir(parents=True, exist_ok=True)
for name in ["kokoro-v1.0.onnx", "voices-v1.0.bin"]:          # ~340 MB, only if you don't have them yet
    if not (MODELS / name).exists():
        print(f"Downloading {name} into {MODELS} (once, please wait)...")
        urllib.request.urlretrieve(URL + name, MODELS / (name + ".part"))
        (MODELS / (name + ".part")).rename(MODELS / name)

print("Loading ears, voice detector and mouth...")
ears = WhisperModel("base", device="cpu", compute_type="int8")
mouth = Kokoro(str(MODELS / "kokoro-v1.0.onnx"), str(MODELS / "voices-v1.0.bin"))
vad = VADIterator(load_silero_vad(), threshold=0.5, sampling_rate=RATE,
                  min_silence_duration_ms=700)                 # 0.7 s of quiet = you finished
mic = queue.Queue()


def speak(text):
    samples, rate = mouth.create(text, voice=VOICE, speed=1.1, lang="en-us")
    sd.play(samples, rate)
    sd.wait()


def forget_what_the_mic_heard():
    """While the agent talks, the mic keeps recording. Throw that away so it doesn't hear itself."""
    while not mic.empty():
        mic.get_nowait()
    vad.reset_states()


def handle(speech):
    audio = np.concatenate(speech)
    if len(audio) < RATE // 2:                                  # under half a second: a cough or a click
        return
    segments, _ = ears.transcribe(audio, beam_size=1, language="en")
    heard = " ".join(s.text.strip() for s in segments).strip()
    if not heard:
        return
    print("🧑", heard)
    reply = ask(heard)
    print("🤖", reply)
    speak(reply)
    if "goodbye" in heard.lower():
        raise KeyboardInterrupt                                 # leave the main loop the same way as Ctrl+C


before = deque(maxlen=10)                 # the last 0.3 s, so your first syllable isn't cut off
speech, talking = [], False
print(f"🎧 Just talk (brain: {MODEL}). Say 'goodbye' or press Ctrl+C to stop.")
try:
    with sd.InputStream(samplerate=RATE, channels=1, dtype="float32", blocksize=CHUNK,
                        callback=lambda chunk, *_: mic.put(chunk[:, 0].copy())):
        while True:
            if not talking and not timer_alerts.empty():       # a timer rang while you were quiet
                speak(timer_alerts.get())
                forget_what_the_mic_heard()
            try:
                chunk = mic.get(timeout=0.5)                    # wait at most 0.5 s, then check timers again
            except queue.Empty:
                continue
            event = vad(torch.from_numpy(chunk))                # None, {"start": ...} or {"end": ...}
            if event and "start" in event:
                talking, speech = True, list(before)
                print("🟢 listening...", end="\r")
            if talking:
                speech.append(chunk)
            else:
                before.append(chunk)
            if event and "end" in event:
                talking = False
                handle(speech)
                forget_what_the_mic_heard()
except KeyboardInterrupt:
    print("\n👋 Bye!")
