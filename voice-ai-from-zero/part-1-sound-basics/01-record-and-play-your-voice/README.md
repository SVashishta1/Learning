# 01 · Record and play your voice

**What it does:** records 5 seconds from your microphone, plays it back, and saves `my_voice.wav`. That file is what you'll feed to the AI models later.

## Run it
```bash
cd part-1-sound-basics/01-record-and-play-your-voice
python record.py
```
(If no sound is recorded, check your system's microphone permission for the terminal or VS Code.)

## The idea in one sentence
Sound = a list of numbers between -1 and 1; **16,000 numbers per second** is called the *sample rate*, and 16 kHz is what speech models like Whisper expect.

## Try this
1. Change `SECONDS` to 10.
2. Change `SAMPLE_RATE` to 8000 (old telephone quality) and to 44100 (CD quality). Can you hear the difference?
3. Run `python -m sounddevice` to list your microphones and speakers.
