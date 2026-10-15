# Detect what language someone speaks, write it down in that language, AND translate it to English.
# Usage: python translate_speech.py spanish_clip.mp3
import sys
from pathlib import Path

from faster_whisper import WhisperModel

path = sys.argv[1] if len(sys.argv) > 1 else "../../part-1-sound-basics/01-record-and-play-your-voice/my_voice.wav"
if not Path(path).exists():
    sys.exit(f"Can't find {path}. Pass a recording: python translate_speech.py my_clip.mp3")
model = WhisperModel("small", device="cpu", compute_type="int8")     # 'small' or bigger is much better at other languages

original, info = model.transcribe(path, task="transcribe")          # info is ready at once: the language is detected first
print(f"🌍 Detected language: {info.language} ({info.language_probability:.0%} sure)\n")
print("📝 What they said:")
print("  ", " ".join(s.text.strip() for s in original))

if info.language != "en":
    english, _ = model.transcribe(path, task="translate")           # Whisper can translate any language → English
    print("\n🇬🇧 In English:")
    print("  ", " ".join(s.text.strip() for s in english))
else:
    print("\n(It's already English, so there is nothing to translate.)")
