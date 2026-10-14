# Make your computer talk using the voices already built into it (Windows, Mac and Linux). Instant and offline.
# Usage: python speak.py "Hello, I am your computer."
import sys

import pyttsx3

text = " ".join(sys.argv[1:]) or "Hello! I am your computer. I can talk without the internet."
engine = pyttsx3.init()

voices = engine.getProperty("voices")
print(f"Your computer has {len(voices)} voices:")
for i, v in enumerate(voices[:10]):
    print(f"  {i}: {v.name}")

engine.setProperty("rate", 170)               # words per minute (default ~200)
engine.setProperty("voice", voices[0].id)     # try other numbers from the list above
engine.say(text)
engine.save_to_file(text, "computer_voice.wav")
engine.runAndWait()
print("🔊 Done (also saved computer_voice.wav)")
