# Natural-sounding speech with Piper, a small, fast neural voice that runs on any computer (even a Raspberry Pi).
# Usage: python piper_speak.py "Hello from Piper!"            (first download a voice, see the README)
import sys
import time
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
voice = PiperVoice.load(VOICE)                # also reads en_US-lessac-medium.onnx.json (the voice's settings)

start = time.time()
with wave.open("piper.wav", "wb") as wav_file:          # an empty WAV file that Piper fills in
    voice.synthesize_wav(text, wav_file)
made_in = time.time() - start
audio, rate = sf.read("piper.wav")
print(f"Saved piper.wav: {len(audio) / rate:.1f} s of speech, made in {made_in:.2f} s")

# Same text, slower and more expressive: length_scale > 1 = slower, noise_scale = more variation
with wave.open("piper_slow.wav", "wb") as wav_file:
    voice.synthesize_wav(text, wav_file, syn_config=SynthesisConfig(length_scale=1.3, noise_scale=0.8))
print("Saved piper_slow.wav (slower, more expressive)")

print("🔊 Playing piper.wav, then piper_slow.wav...")
sd.play(audio, rate)
sd.wait()
slow, rate = sf.read("piper_slow.wav")
sd.play(slow, rate)
sd.wait()
