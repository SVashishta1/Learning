# Detect what language someone speaks, write it down in that language, AND translate it to English.
# Usage: python translate_speech.py spanish_clip.mp3
import sys

from faster_whisper import WhisperModel

path = sys.argv[1] if len(sys.argv) > 1 else "../../part-1-sound-basics/01-record-and-play-your-voice/my_voice.wav"
model = WhisperModel("small", device="cpu", compute_type="int8")     # 'small' or bigger is much better at other languages

original, info = model.transcribe(path, task="transcribe")
print(f"🌍 Detected language: {info.language} ({info.language_probability:.0%} sure)\n")
print("📝 What they said:")
print("  ", " ".join(s.text.strip() for s in original))

if info.language != "en":
    english, _ = model.transcribe(path, task="translate")           # Whisper can translate any language → English
    print("\n🇬🇧 In English:")
    print("  ", " ".join(s.text.strip() for s in english))
