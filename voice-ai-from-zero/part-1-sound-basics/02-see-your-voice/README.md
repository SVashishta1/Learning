# 02 · See your voice

**What it does:** draws your recording as a **wave** and as a **spectrogram** (a heat-map of pitches over time, the "picture" speech AI actually looks at), and prints a loudness bar so you can spot silence vs. speech.

## Run it
```bash
cd part-1-sound-basics/02-see-your-voice
python see_voice.py
```
Open `my_voice.png`.

## The idea in one sentence
Whisper doesn't "listen". It turns audio into a spectrogram-like picture (a *log-Mel spectrogram*) and reads it the way an image model reads a photo.

## Try this
1. Record yourself whistling a rising note (project 01), then look for a bright line climbing in the spectrogram.
2. Say "sssss" and then "mmmmm". Where does each show up, high or low?
