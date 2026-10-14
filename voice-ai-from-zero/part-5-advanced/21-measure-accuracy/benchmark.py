# Which Whisper size should I use? Measure it: accuracy (Word Error Rate) and speed, on clean and noisy audio.
# Trick: Kokoro reads sentences we already know, so we have the "correct answers" without recording anything.
import re
import time
import urllib.request
from pathlib import Path

import jiwer
import numpy as np
from faster_whisper import WhisperModel
from kokoro_onnx import Kokoro
from scipy.signal import resample_poly

SIZES = ["tiny", "base", "small"]
SENTENCES = [
    "The quick brown fox jumps over the lazy dog.",
    "Please book a table for four people at seven thirty tomorrow evening.",
    "My flight to Barcelona leaves from gate twelve at noon.",
    "Turn off the kitchen lights and set an alarm for six in the morning.",
    "Machine learning models need a lot of good quality data.",
    "She sells seashells by the seashore on sunny Saturdays.",
]
KOKORO = "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/"
for name in ["kokoro-v1.0.onnx", "voices-v1.0.bin"]:
    if not Path(name).exists():
        urllib.request.urlretrieve(KOKORO + name, name)


def clean(text):
    """Ignore capitals and punctuation when comparing: 'Hello, World!' == 'hello world'."""
    return re.sub(r"[^a-z0-9' ]", "", text.lower()).strip()


# 1. Make the test audio: each sentence in a different voice, then a noisy copy
kokoro = Kokoro("kokoro-v1.0.onnx", "voices-v1.0.bin")
voices = ["af_heart", "am_adam", "bf_emma", "bm_george", "af_nicole", "am_michael"]
clips = []
for sentence, voice in zip(SENTENCES, voices):
    samples, rate = kokoro.create(sentence, voice=voice, lang="en-us")
    clips.append(resample_poly(samples, 2, 3).astype(np.float32))    # 24 kHz -> 16 kHz for Whisper
noise = np.random.default_rng(0)
tests = {"clean": clips,
         "noisy": [c + 0.05 * noise.standard_normal(len(c)).astype(np.float32) for c in clips]}
audio_seconds = sum(len(c) for c in clips) / 16000

# 2. Run every model on every clip
print(f"{'model':8} {'audio':6} {'WER':>6} {'speed':>12}")
for size in SIZES:
    model = WhisperModel(size, device="cpu", compute_type="int8")
    for condition, audios in tests.items():
        start = time.time()
        heard = [" ".join(s.text for s in model.transcribe(a, language="en", beam_size=1)[0]) for a in audios]
        seconds = time.time() - start
        wer = jiwer.wer([clean(s) for s in SENTENCES], [clean(h) for h in heard])
        print(f"{size:8} {condition:6} {wer:6.1%} {audio_seconds / seconds:9.1f}x RT")
        for truth, guess in zip(SENTENCES, heard):
            if clean(truth) != clean(guess):
                print(f"         ✗ {guess.strip()}")
