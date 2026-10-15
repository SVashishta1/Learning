# Step 2: hands-free listening. Silero VAD says exactly when you start and stop talking,
# so we transcribe whole sentences, ignore noise, and never need a button.
from collections import deque
import queue

import numpy as np
import sounddevice as sd
import torch
from faster_whisper import WhisperModel
from silero_vad import VADIterator, load_silero_vad

RATE, CHUNK = 16000, 512                # Silero listens to 512 samples (32 ms) at a time
vad = VADIterator(load_silero_vad(), threshold=0.5, sampling_rate=RATE,
                  min_silence_duration_ms=600)            # 0.6 s of quiet = you finished
whisper = WhisperModel("base", device="cpu", compute_type="int8")
mic = queue.Queue()
before = deque(maxlen=10)               # the last 0.3 s, so the first syllable isn't cut off
speech, talking = [], False

print("🎧 Just talk. (Ctrl+C to stop)")
try:
    with sd.InputStream(samplerate=RATE, channels=1, dtype="float32", blocksize=CHUNK,
                        callback=lambda chunk, *_: mic.put(chunk[:, 0].copy())):
        while True:
            chunk = mic.get()
            event = vad(torch.from_numpy(chunk))              # None, {"start": ...} or {"end": ...}
            if event and "start" in event:
                talking, speech = True, list(before)          # start with the 0.3 s before the voice began
                print("🟢 speaking...", end="\r")
            if talking:
                speech.append(chunk)
            else:
                before.append(chunk)
            if event and "end" in event:
                talking = False
                segments, _ = whisper.transcribe(np.concatenate(speech), beam_size=1)
                print("📝", " ".join(s.text.strip() for s in segments), " " * 10)
except KeyboardInterrupt:
    print("\n👋 Stopped.")
