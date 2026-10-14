# Live transcription: listens to your microphone and writes down what you say, sentence by sentence.
# Uses faster-whisper: the same Whisper model, rebuilt to run ~4x faster on a normal CPU.
import queue

import numpy as np
import sounddevice as sd
from faster_whisper import WhisperModel

RATE = 16000
model = WhisperModel("base", device="cpu", compute_type="int8")   # int8 = smaller numbers = faster on CPU
heard = queue.Queue()


def on_audio(chunk, frames, time, status):        # the microphone calls this ~10 times a second
    heard.put(chunk[:, 0].copy())


print("🎙️  Speak! (Ctrl+C to stop). I write each phrase after you pause.\n")
buffer, silent_chunks = [], 0
with sd.InputStream(samplerate=RATE, channels=1, dtype="float32", blocksize=RATE // 10, callback=on_audio):
    while True:
        chunk = heard.get()
        buffer.append(chunk)
        loud = np.sqrt(np.mean(chunk ** 2)) > 0.01                 # is anyone speaking in this 0.1 s?
        silent_chunks = 0 if loud else silent_chunks + 1
        speech_seconds = len(buffer) / 10
        # Transcribe when you pause for 0.7 s (after saying something), or every 15 s at most
        if (silent_chunks >= 7 and speech_seconds > 1) or speech_seconds > 15:
            audio = np.concatenate(buffer)
            buffer, silent_chunks = [], 0
            segments, _ = model.transcribe(audio, language="en", vad_filter=True, beam_size=1)
            text = " ".join(s.text.strip() for s in segments)
            if text:
                print("📝", text)
        elif not loud and len(buffer) > 20 and silent_chunks == len(buffer):
            buffer, silent_chunks = [], 0                            # throw away long silences
