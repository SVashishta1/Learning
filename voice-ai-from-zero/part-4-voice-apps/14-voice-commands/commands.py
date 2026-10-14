# Voice commands: say "open YouTube", "search for pizza", "timer 2 minutes", "what time is it", "note buy milk".
# Listens like project 05, then matches what you said against simple rules. No AI needed for the "brain"!
import queue
import re
import threading
import webbrowser
from datetime import datetime

import numpy as np
import pyttsx3
import sounddevice as sd
from faster_whisper import WhisperModel

RATE = 16000
SITES = {"youtube": "https://youtube.com", "google": "https://google.com",
         "wikipedia": "https://wikipedia.org", "gmail": "https://mail.google.com"}
NUMBERS = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "ten": 10, "twenty": 20, "thirty": 30}


def say(text):
    print("🤖", text)
    engine = pyttsx3.init()
    engine.say(text)
    engine.runAndWait()


def handle(text):
    """Turn what you said into an action. Returns the reply, or None if it's not a command."""
    t = re.sub(r"[^\w\s]", "", text.lower())          # "Open YouTube!" -> "open youtube"
    if "time" in t and "timer" not in t:
        return "It's " + datetime.now().strftime("%I:%M %p")
    if "search for" in t:
        query = t.split("search for", 1)[1].strip()
        webbrowser.open("https://www.google.com/search?q=" + query.replace(" ", "+"))
        return "Searching for " + query
    if "open" in t:
        for name, url in SITES.items():
            if name in t:
                webbrowser.open(url)
                return "Opening " + name
    if "timer" in t:
        match = re.search(r"(\d+|" + "|".join(NUMBERS) + r")\s*(second|minute)", t)
        if match:
            word = match.group(1)
            amount = int(word) if word.isdigit() else NUMBERS[word]
            seconds = amount * (60 if match.group(2) == "minute" else 1)
            threading.Timer(seconds, say, ["⏰ Time's up!"]).start()
            return f"Timer set for {amount} {match.group(2)}s"
    if t.startswith("note"):
        with open("notes.txt", "a", encoding="utf-8") as f:
            f.write(datetime.now().strftime("%Y-%m-%d %H:%M ") + text[4:].strip(" ,.:") + "\n")
        return "Noted"
    if "goodbye" in t or "stop listening" in t:
        say("Goodbye!")
        raise SystemExit
    return None


def listen():
    """Yields each phrase you say (same pause trick as project 05)."""
    model = WhisperModel("base.en", device="cpu", compute_type="int8")   # .en = English-only, a bit more accurate
    heard = queue.Queue()
    buffer, silent = [], 0
    with sd.InputStream(samplerate=RATE, channels=1, dtype="float32", blocksize=RATE // 10,
                        callback=lambda chunk, *_: heard.put(chunk[:, 0].copy())):
        while True:
            chunk = heard.get()
            buffer.append(chunk)
            silent = 0 if np.sqrt(np.mean(chunk ** 2)) > 0.01 else silent + 1
            if silent >= 7 and len(buffer) > 10:
                segments, _ = model.transcribe(np.concatenate(buffer), language="en", vad_filter=True)
                buffer, silent = [], 0
                text = " ".join(s.text.strip() for s in segments)
                if text:
                    yield text
            elif silent == len(buffer) and len(buffer) > 20:
                buffer, silent = [], 0


if __name__ == "__main__":
    print("🎙️  Try: 'open YouTube', 'search for pizza', 'timer 10 seconds', 'what time is it', 'note call mum', 'goodbye'")
    for phrase in listen():
        print("👂", phrase)
        reply = handle(phrase)
        if reply:
            say(reply)
