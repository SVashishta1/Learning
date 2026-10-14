# 06 · Subtitles for any video

**What it does:** creates a `.srt` subtitle file for any video or podcast. Put it next to the video and players like **VLC** show subtitles automatically.

## Run it
```bash
cd part-2-speech-to-text/06-subtitles-for-any-video
python make_subtitles.py "my video.mp4"
```
Use any video from your phone or a downloaded lecture. A 10-minute video takes a few minutes on a laptop.

## The idea in one sentence
Whisper gives every phrase a **start and end time**; an `.srt` file is just those times plus the text, in a simple format any video player understands.

## Try this
1. Open the `.srt` file in a text editor and look at the format.
2. Add `task="translate"` to `model.transcribe(...)` to make **English** subtitles for a video in another language.
3. Split subtitles longer than 42 characters into two lines (the TV standard).
