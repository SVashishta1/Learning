# 14 · Voice commands

**What you'll build:** control your computer by voice. Say "what time is it", "open YouTube", "search for pizza recipes", "set a timer for 2 minutes", "note call mum", and finally "goodbye". It answers out loud with your computer's built-in voice.
**Like you're 10:** Whisper writes down what you said, then a list of "if you hear this word, do that" rules decides what to do.
**Time:** ~1.5 h · **Builds on:** [13 · Voice notes app](../13-voice-notes-app), the live listener from [05](../../part-2-speech-to-text/05-faster-whisper-live-microphone) and the voice from [09](../../part-3-text-to-speech/09-your-computer-speaks) · **Needs:** a microphone, speakers (headphones recommended)

## Why this matters
Many real voice features ("Hey Google, set a timer", car voice controls, smart-TV remotes) use exactly this design for simple commands: speech-to-text plus **rules** (also called **intents**). Rules are fast, predictable, free and work offline. Knowing when simple rules are enough, and when you need an LLM (project 15), is an important engineering judgement.

## What you'll learn
- **Intent**: what the user wants ("set a timer"), recognised here by keywords.
- **Slot**: a detail inside the request (the "2 minutes"), pulled out with a **regular expression** (a text pattern).
- **Generator (`yield`)**: `listen()` hands out phrases one at a time, forever, so the main loop reads like "for each phrase you say...".
- **Background timer (`threading.Timer`)**: run a function later without stopping the program.
- **Echo problem**: a voice app must not react to its own voice; here we mute the microphone while the computer talks.

## Before you start
Same install as the rest of Part 4 (skip if done):
```bash
pip install faster-whisper "av<19" kokoro-onnx fastapi uvicorn python-multipart httpx pyttsx3 sounddevice soundfile numpy
```
- `faster-whisper`: speech to text. `sounddevice` + `numpy`: the microphone and loudness check, and the timer beep.
- `pyttsx3`: the computer's built-in voice for replies (Linux: also `sudo apt install espeak-ng`).

No API key needed. The first run downloads Whisper `base.en` (~145 MB).

## Run it
1. From the course folder:
   ```bash
   cd part-4-voice-apps/14-voice-commands
   python commands.py
   ```
2. Wait for the 🎙️ line, then say one command, pause, and wait for the reply before the next one:
   - "What time is it?"
   - "Open YouTube." (also: Google, Wikipedia, Gmail)
   - "Search for pizza recipes."
   - "Set a timer for 10 seconds."
   - "Note, call mum tomorrow." (saved in `notes.txt`)
   - "Goodbye." (or press `Ctrl+C`)

### What you should see
We fed it a recording of these six commands:
```
🎙️  Try: 'open YouTube', 'search for pizza', 'timer 10 seconds', 'what time is it', 'note call mum', 'goodbye'
👂 What time is it?
🤖 It's 04:16 AM
👂 Open YouTube.
🤖 Opening youtube
👂 Search for pizza recipes
🤖 Searching for pizza recipes
👂 Set a timer for three seconds.
🤖 Timer set for 3 seconds
👂 Note call mum tomorrow.
🤖 Noted
⏰ Time's up!
👂 Goodbye.
🤖 Goodbye!
```
👂 lines are what Whisper heard; 🤖 lines are the replies (also spoken). YouTube and the Google search open in your browser, you hear a beep when the timer ends, and `notes.txt` now contains `2026-10-15 04:16 call mum tomorrow`. Anything that isn't a command is printed with 👂 and ignored.

## How it works
Open `commands.py`. Read it from the bottom (`if __name__ == "__main__":`) up.

1. **The main loop**: `for phrase in listen():` gets each phrase, prints it, passes it to `handle(phrase)`, and speaks the reply with `say(...)` if there is one. `except KeyboardInterrupt` catches `Ctrl+C`.
2. **`listen()`** is project 05's pause detector turned into a **generator**: instead of printing, it does `yield text`. The `for` loop receives that text, runs its body, then `listen()` continues where it stopped. The microphone callback `on_audio` only adds sound to the queue when `muted` is `False`.
3. **`say(text)`** prints the reply, sets `muted = True`, speaks with pyttsx3, then sets `muted = False`. Without this, the microphone would hear "Timer set for 3 seconds" from the speakers... and set another timer.
4. **`handle(text)`** is the "brain": a list of `if` rules, checked in order. First it cleans the text: `.lower()` and `re.sub(r"[^\w\s]", "", ...)` remove capitals and punctuation, so "Open YouTube!" becomes `"open youtube"`.
   - **time**: contains "time" but not "timer" → `datetime.now().strftime("%I:%M %p")` makes "04:16 AM".
   - **search**: everything after "search for" becomes the query in a Google URL; `webbrowser.open(...)` opens your default browser.
   - **open**: looks for a site name from the `SITES` dictionary.
   - **timer**: the regular expression `\b(\d+|one|two|...)\s*(second|minute)` means "a number (as digits or a word), maybe a space, then 'second' or 'minute'". `match.group(1)` is the number, `match.group(2)` the unit. `threading.Timer(seconds, ring)` will call `ring()` later in the background; `daemon = True` means a pending timer won't stop the program from quitting.
   - **note**: if the phrase starts with "note", the rest is appended to `notes.txt` with the date.
   - **goodbye**: says goodbye and `raise SystemExit` ends the program.
   - Nothing matched → `return None`, and the main loop stays quiet.
5. **`ring()`** prints "Time's up" and plays a beep: `np.sin(...)` makes half a second of an 880 Hz tone (a high A note), and `sd.play(...)` plays it.

```
mic ──▶ listen(): pause detection + Whisper ──▶ "Open YouTube." ──▶ handle(): rules ──▶ webbrowser.open(...)
  ▲                                                                       │
  └──────── muted while ◀── say("Opening youtube") ◀─────────────────────┘
```

## If something goes wrong
- **It reacts to things you didn't say, or hears itself** → use headphones, or raise the loudness threshold `0.01` to `0.02`.
- **"Open YouTube" is heard but nothing opens** → Whisper may have written "You Tube" or "Youtube's". Print `t` inside `handle` to see the cleaned text, and adjust the keyword (e.g. add `"you tube": "https://youtube.com"` to `SITES`).
- **Timers like "two and a half minutes" don't work** → the rule only understands whole numbers and the words in `NUMBERS`. That's the limit of rules (see project 15).
- **Linux: `RuntimeError: ... eSpeak ...`** → `sudo apt install espeak-ng`.
- **No beep when a timer ends** → check the default output device (`python -m sounddevice`).

## Try this
1. **Easy:** add your own website to `SITES`, for example your favourite news site.
   <details><summary>Hint</summary>Add an entry like <code>"bbc": "https://bbc.co.uk"</code> to the <code>SITES</code> dictionary, then say "Open BBC". Keys must be lower-case, because the text is lower-cased before matching.</details>
2. **Medium:** add a **wake word**: only react to phrases that start with "computer" ("Computer, what time is it?"). Now it ignores normal conversation.
   <details><summary>Solution</summary>

   At the start of `handle`, right after the `t = re.sub(...)` line:
   ```python
   if not t.startswith("computer"):
       return None
   t = t[len("computer"):].strip()      # remove the wake word, then check the rules as before
   ```
   Note that the "note" rule uses the original `text`, so for notes you'll also want to cut "computer" from `text`. Real wake words ("Hey Siri") use a tiny always-on model instead of Whisper, so they use almost no battery.
   </details>
3. **Harder:** add a command "read my notes" that reads `notes.txt` aloud.
   <details><summary>Solution</summary>

   Add this rule in `handle`, **before** the `if t.startswith("note"):` rule:
   ```python
   if "read my notes" in t:
       try:
           lines = open("notes.txt", encoding="utf-8").read().splitlines()
       except FileNotFoundError:
           return "You have no notes yet"
       return "Your notes: " + ". ".join(line[17:] for line in lines)   # [17:] skips the date and time
   ```
   The order matters: rules are checked top to bottom, and the first match wins.
   </details>

## Check yourself
1. What is the difference between an intent and a slot? Give an example from this project.
2. Why is the mic muted while the computer speaks?
3. What does `yield` let `listen()` do that `return` couldn't?
4. Give one command that rules handle badly, and why an LLM (project 15) would do better.

<details><summary>Answers</summary>

1. The intent is what you want (set a timer); the slot is a detail inside it (3 seconds).
2. Otherwise the microphone hears the reply through the speakers, Whisper transcribes it, and the program might react to its own words (for example setting a new timer).
3. Hand out one phrase at a time and then continue listening, forever. `return` would end the function after the first phrase.
4. For example "remind me in a quarter of an hour" or "what's on YouTube?": the words don't match the fixed patterns. An LLM understands meaning, not just keywords, but it's slower and less predictable.
</details>

## Learn more (optional)
- Python regular expressions, a gentle guide: https://docs.python.org/3/howto/regex.html
- Practise regex patterns online: https://regex101.com
- Search YouTube for "how wake word detection works".

## Next
→ [15 · Talk to a local AI](../15-talk-to-a-local-ai)
