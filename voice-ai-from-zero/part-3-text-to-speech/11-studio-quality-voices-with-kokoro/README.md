# 11 · Studio-quality voices with Kokoro

**What it does:** speaks with **Kokoro-82M**, one of the most natural open-source voices available. It has 50+ voices (American, British and other languages), runs on a normal CPU, and you can **mix two voices** into a new one.

## Run it
```bash
cd part-3-text-to-speech/11-studio-quality-voices-with-kokoro
python kokoro_speak.py
python kokoro_speak.py "Welcome to my podcast about AI." am_michael
```
The first run downloads ~350 MB of model files.

## The idea in one sentence
Each voice is stored as a small list of numbers (a "style vector"), so mixing 50% of one voice with 50% of another literally averages two lists and creates a voice that never existed.

## Try this
1. Try `bf_emma`, `am_adam`, `af_bella` and `bm_george`.
2. Make a 70/30 mix instead of 50/50.
3. Read a whole text file aloud: `open("story.txt").read()`. Kokoro splits long text into sentences automatically.
