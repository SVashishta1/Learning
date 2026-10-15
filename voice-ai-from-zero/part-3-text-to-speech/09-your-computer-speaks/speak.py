# Make your computer talk using the voices already built into it (Windows, Mac and Linux). Instant and offline.
# Usage: python speak.py "Hello, I am your computer."
import sys

import pyttsx3

VOICE_NUMBER = None        # None = the first English voice. Or put a number from the list, e.g. 3
text = " ".join(sys.argv[1:]) or "Hello! I am your computer. I can talk without the internet."
engine = pyttsx3.init()    # connects to your system's speech engine (SAPI5, NSSpeechSynthesizer or eSpeak)

voices = engine.getProperty("voices")
# Each voice has language codes like "en-US" or "fr-FR". Keep the numbers of the English ones.
english = [i for i, v in enumerate(voices) if any(str(lang).lower().startswith("en") for lang in v.languages)]
print(f"Your computer has {len(voices)} voices. The English ones:")
for i in english[:10]:
    print(f"  {i}: {voices[i].name}")

if VOICE_NUMBER is None:
    VOICE_NUMBER = english[0] if english else 0
print(f"Using voice {VOICE_NUMBER}: {voices[VOICE_NUMBER].name}")

engine.setProperty("rate", 170)                          # words per minute (default ~200)
engine.setProperty("voice", voices[VOICE_NUMBER].id)
engine.say(text)                                         # queue: speak it out loud...
engine.save_to_file(text, "computer_voice.wav")          # ...and also save it as a file
engine.runAndWait()                                      # now do everything in the queue, and wait until it's done
print("🔊 Done (also saved computer_voice.wav)")
