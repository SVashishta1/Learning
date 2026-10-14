# 14 · Voice commands

**What it does:** control your computer by voice: "open YouTube", "search for pizza recipes", "timer 2 minutes", "what time is it", "note call mum", "goodbye".

## Run it
```bash
cd part-4-voice-apps/14-voice-commands
python commands.py
```

## The idea
`listen()` turns speech into text (Whisper). `handle()` is just **if-statements** looking for keywords. Many real voice products work exactly like this for simple commands: fast, predictable and offline. In project 15 we swap the if-statements for an LLM.

## Try this
1. Add a **wake word**: ignore phrases that don't start with "computer" (`if not t.startswith("computer"): return None`). Now it won't react to normal talk.
2. Add your own site to `SITES`, and a command "read my notes" that speaks `notes.txt`.
3. Add "play music": `webbrowser.open("https://music.youtube.com")`.
