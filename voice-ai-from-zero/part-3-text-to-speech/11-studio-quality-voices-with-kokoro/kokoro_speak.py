# Very natural speech with Kokoro-82M (Apache licence): 50+ voices, runs offline on a normal CPU.
# Usage: python kokoro_speak.py "Text to say" af_heart
import sys
import time
import urllib.request
from pathlib import Path

import numpy as np
import sounddevice as sd
import soundfile as sf
from kokoro_onnx import Kokoro

# The model files are shared by every project in this course: they live in voice-ai-from-zero/models/
MODELS = Path(__file__).resolve().parents[2] / "models"
URL = "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/"
MODELS.mkdir(exist_ok=True)
for name in ["kokoro-v1.0.onnx", "voices-v1.0.bin"]:             # ~310 MB + ~27 MB, downloaded once
    if not (MODELS / name).exists():
        print(f"Downloading {name} into {MODELS} (once, please wait)...")
        urllib.request.urlretrieve(URL + name, MODELS / (name + ".part"))
        (MODELS / (name + ".part")).rename(MODELS / name)          # only "finished" files get the real name

kokoro = Kokoro(str(MODELS / "kokoro-v1.0.onnx"), str(MODELS / "voices-v1.0.bin"))
text = sys.argv[1] if len(sys.argv) > 1 else "Hi! I'm Kokoro. I run completely on your computer, and I sound almost human."
voice = sys.argv[2] if len(sys.argv) > 2 else "af_heart"

print("Some voices:", ", ".join(sorted(kokoro.get_voices())[:12]), "...")
# Names: first letter = accent (a = American, b = British), second = f/m (female/male)
start = time.time()
samples, rate = kokoro.create(text, voice=voice, speed=1.0, lang="en-us")
sf.write("kokoro.wav", samples, rate)
print(f"🔊 {voice}: {len(samples) / rate:.1f} s of speech, made in {time.time() - start:.1f} s → kokoro.wav")
sd.play(samples, rate)
sd.wait()

# Bonus: MIX two voices to invent a new one (a voice is just a list of numbers!)
mixed = np.add(kokoro.get_voice_style("af_heart") * 0.5, kokoro.get_voice_style("bf_emma") * 0.5)
samples, rate = kokoro.create("And this is a brand new voice, made by mixing two others.", voice=mixed, lang="en-us")
sf.write("kokoro_mixed.wav", samples, rate)
print("🔊 mixed voice (50% af_heart + 50% bf_emma) → kokoro_mixed.wav")
sd.play(samples, rate)
sd.wait()
