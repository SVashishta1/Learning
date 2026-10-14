# Clone YOUR OWN voice with F5-TTS: record a 10-second sample, then make it say anything.
# Usage: python clone_voice.py "Text to say in my voice"
import sys
from pathlib import Path

import sounddevice as sd
import soundfile as sf

CONSENT = "I am recording my own voice, and I agree to clone it for my personal learning project."
SAMPLE = "my_reference.wav"

# Step 1: the voice sample. The sentence doubles as your consent, recorded in your own voice.
if not Path(SAMPLE).exists():
    input(f"Press Enter, then read this out loud, calmly and clearly (10 seconds):\n\n   {CONSENT}\n")
    audio = sd.rec(10 * 24000, samplerate=24000, channels=1)
    sd.wait()
    sf.write(SAMPLE, audio, 24000)
    print(f"Saved {SAMPLE}. (Delete it to record again.)")

# Step 2: generate new speech in that voice
from f5_tts.api import F5TTS          # imported here because it's big and slow to load

text = sys.argv[1] if len(sys.argv) > 1 else \
    "Hello! This isn't really me. It's an AI copy of my voice, made entirely on my own computer."
f5 = F5TTS()                           # downloads the model once (~1.3 GB)
f5.infer(ref_file=SAMPLE, ref_text=CONSENT, gen_text=text, file_wave="cloned.wav", remove_silence=True)

print("🔊 cloned.wav")
speech, rate = sf.read("cloned.wav")
sd.play(speech, rate)
sd.wait()
