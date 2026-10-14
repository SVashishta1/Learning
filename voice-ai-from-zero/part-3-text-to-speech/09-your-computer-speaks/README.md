# 09 · Your computer speaks

**What it does:** reads any text aloud using the voices already built into your operating system, and lists the voices you have.

## Run it
```bash
cd part-3-text-to-speech/09-your-computer-speaks
python speak.py "I am learning voice AI."
```

## The idea in one sentence
Every OS ships a basic speech engine (SAPI on Windows, NSSpeechSynthesizer on Mac, eSpeak on Linux); `pyttsx3` is one Python API for all of them. It's instant, but sounds robotic compared with the neural voices next.

## Try this
1. Try every voice in the list (change `voices[0]`).
2. Set `rate` to 100 and to 300.
