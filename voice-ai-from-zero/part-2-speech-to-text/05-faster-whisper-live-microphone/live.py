# Live transcription: listens to your microphone and writes down what you say, sentence by sentence.
# Uses faster-whisper: the same Whisper model, rebuilt to run ~4x faster on a normal CPU.
import queue

import numpy as np
import sounddevice as sd
from faster_whisper import WhisperModel

RATE = 16000
model = WhisperModel("base", device="cpu", compute_type="int8")   # int8 = smaller numbers = faster on CPU
heard = queue.Queue()                                               # a waiting line between the microphone and us


def on_audio(chunk, frames, time, status):        # the microphone calls this 10 times a second
    heard.put(chunk[:, 0].copy())                 # copy column 0 (mono) into the queue


print("🎙️  Speak! (Ctrl+C to stop). I write each phrase after you pause.\n")
buffer, silent_chunks, spoke = [], 0, False
try:
    with sd.InputStream(samplerate=RATE, channels=1, dtype="float32", blocksize=RATE // 10, callback=on_audio):
        while True:
            chunk = heard.get()                                        # wait for the next 0.1 s of sound
            buffer.append(chunk)
            loud = np.sqrt(np.mean(chunk ** 2)) > 0.01                 # is anyone speaking in this 0.1 s?
            if loud:
                spoke, silent_chunks = True, 0
            else:
                silent_chunks += 1
            if not spoke:
                buffer = buffer[-3:]                                   # only silence so far: keep just the last 0.3 s
            elif silent_chunks >= 7 or len(buffer) >= 150:            # a 0.7 s pause, or 15 s of non-stop talk
                audio = np.concatenate(buffer)
                buffer, silent_chunks, spoke = [], 0, False
                segments, _ = model.transcribe(audio, language="en", vad_filter=True, beam_size=1)
                text = " ".join(s.text.strip() for s in segments)
                if text:
                    print("📝", text)
except KeyboardInterrupt:
    print("\n👋 Stopped.")
