# Natural-sounding speech with Piper, a small, fast neural voice that runs on any computer (even a Raspberry Pi).
# Usage: python piper_speak.py "Hello from Piper!"            (first download a voice, see the README)
import sys
import wave
from pathlib import Path

import sounddevice as sd
import soundfile as sf
from piper import PiperVoice
from piper.config import SynthesisConfig

VOICE = "en_US-lessac-medium.onnx"            # downloaded with: python -m piper.download_voices en_US-lessac-medium
if not Path(VOICE).exists():
    sys.exit("First download a voice:  python -m piper.download_voices en_US-lessac-medium")

text = " ".join(sys.argv[1:]) or "Hello! I'm Piper. I run entirely on your computer, and I sound quite natural."
voice = PiperVoice.load(VOICE)

with wave.open("piper.wav", "wb") as wav_file:
    voice.synthesize_wav(text, wav_file)
print("Saved piper.wav")

# Same text, slower and more expressive: length_scale > 1 = slower, noise_scale = more variation
with wave.open("piper_slow.wav", "wb") as wav_file:
    voice.synthesize_wav(text, wav_file, syn_config=SynthesisConfig(length_scale=1.3, noise_scale=0.8))
print("Saved piper_slow.wav")

audio, rate = sf.read("piper.wav")
sd.play(audio, rate)
sd.wait()
