# 10 · Natural voices with Piper

**What it does:** speaks with a neural voice that sounds far more natural than project 09. It's still tiny (~60 MB) and fast enough for a Raspberry Pi.

## Run it
```bash
cd part-3-text-to-speech/10-natural-voices-with-piper
python -m piper.download_voices en_US-lessac-medium     # once, ~60 MB
python piper_speak.py "Good morning! Here is your daily summary."
```
Browse and listen to all voices (40+ languages): https://rhasspy.github.io/piper-samples/
Download another one by name, e.g. `python -m piper.download_voices en_GB-alan-medium`, then change `VOICE`.

## The idea in one sentence
A neural TTS model turns text into sounds (phonemes) and then into audio samples. Piper is optimised to do this *faster than real time* on a normal CPU.

## Try this
1. Try a British voice and a voice in another language.
2. Change `length_scale` (speed) and `noise_scale` (expressiveness).
3. Command-line version, no Python file needed: `echo "hi there" | python -m piper -m en_US-lessac-medium -f hi.wav`
