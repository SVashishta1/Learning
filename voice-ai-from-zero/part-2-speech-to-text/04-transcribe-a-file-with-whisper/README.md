# 04 · Transcribe a file with Whisper

**What it does:** turns any recording into text, with the language and a time stamp for each sentence, using **OpenAI's open-source Whisper** on your own computer.

## Run it
```bash
cd part-2-speech-to-text/04-transcribe-a-file-with-whisper
python transcribe.py ../../part-1-sound-basics/01-record-and-play-your-voice/my_voice.wav
python transcribe.py my_podcast.mp3 small        # any audio or video file, and a bigger model
```
The first run downloads the model (~140 MB for `base`).

## The idea in one sentence
`whisper.load_model("base")` loads the brain once; `model.transcribe(file)` turns sound into text. It's a 2-line API for something that was a research problem 10 years ago.

## Try this
1. Transcribe the same file with `tiny` and with `small`. Compare speed and mistakes.
2. Record a sentence in another language you know and transcribe it.
3. Record with background music or noise. How well does it cope?
