# 05 · Faster Whisper + live microphone

**What it does:** listens to your microphone non-stop and prints each phrase a moment after you pause. It uses **faster-whisper**, the same Whisper model optimised to run about 4× faster on a normal CPU.

## Run it
```bash
cd part-2-speech-to-text/05-faster-whisper-live-microphone
python live.py
```
Speak a sentence, pause, and watch it appear. Stop with `Ctrl+C`.

## The idea in one sentence
Whisper works on chunks of audio, not a live stream, so we **collect** sound until you pause (a simple loudness check) and then transcribe that chunk. `vad_filter=True` also skips silent parts inside the chunk.

## Try this
1. Change `language="en"` to `None` and speak another language: it detects it automatically.
2. If it cuts you off mid-sentence, raise `silent_chunks >= 7` to `>= 10`. If it triggers on background noise, raise `0.01` to `0.02`.
3. Save every phrase to `diary.txt` with the time. Now you have a voice diary!
