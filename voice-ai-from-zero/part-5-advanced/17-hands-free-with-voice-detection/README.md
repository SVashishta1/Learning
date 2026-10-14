# 17 · Hands-free with voice detection

**What it does:** uses **Silero VAD** (Voice Activity Detection) to know *exactly* when someone is speaking. Our old trick (project 05) only checked loudness, so a door slam or music counted as speech. Silero is a tiny neural network trained to recognise human voices.

## Run it
```bash
cd part-5-advanced/17-hands-free-with-voice-detection
python find_speech.py ../../part-1-sound-basics/01-record-and-play-your-voice/my_voice.wav
python hands_free.py
```
- `find_speech.py`: lists the speech parts of a file. Useful for cutting silence before transcribing long recordings.
- `hands_free.py`: talk naturally; each sentence is printed when you finish it. Clap or play music: it ignores them.

## Key settings
| Setting | Meaning | Raise it if... |
|---------|---------|----------------|
| `threshold=0.5` | how sure it must be that it's a voice | background noise triggers it |
| `min_silence_duration_ms=600` | how long a pause ends your sentence | it cuts you off while you think |

## Try this
1. Replace `record()` in project 15 with this listener: now your AI conversation is hands-free.
2. Print the VAD's speech probability for each chunk (`vad.model(torch.from_numpy(chunk), 16000).item()`) and watch it while you talk, whisper, and clap.
