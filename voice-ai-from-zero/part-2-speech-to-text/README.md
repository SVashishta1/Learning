# Part 2 · Speech to text

**Whisper** is OpenAI's free, open-source speech recogniser. It was trained on 680,000 hours of audio, understands 99 languages, and runs on your own computer.

| # | Project | What you'll have |
|---|---------|------------------|
| 04 | [Transcribe a file with Whisper](04-transcribe-a-file-with-whisper) | any recording → text, using OpenAI's own `whisper` package |
| 05 | [Faster Whisper + live microphone](05-faster-whisper-live-microphone) | 4× faster Whisper, transcribing as you speak |
| 06 | [Subtitles for any video](06-subtitles-for-any-video) | a `.srt` subtitle file for any video or podcast |
| 07 | [Whisper inside the browser](07-whisper-inside-the-browser) | speech-to-text with **no server at all** |
| 08 | [Any language → English](08-any-language-to-english) | detect the language and translate speech to English |

Install once:
```bash
pip install openai-whisper faster-whisper "av<19" sounddevice soundfile numpy
```
**Model sizes:** start with `base`. Bigger = more accurate but slower.

| Size | Download | Speed on a laptop CPU | When to use |
|------|----------|-----------------------|-------------|
| tiny | 75 MB | very fast | quick tests, weak computers |
| base | 140 MB | fast | **default for learning** |
| small | 460 MB | OK | good accuracy |
| medium | 1.5 GB | slow | high accuracy, other languages |
| large-v3 / turbo | 1.6–3 GB | needs a GPU | best quality |
