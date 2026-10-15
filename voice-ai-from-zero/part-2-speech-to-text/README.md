# Part 2 · Speech to text

**Whisper** is OpenAI's free, open-source speech recogniser (MIT licence). It was trained on 680,000 hours of audio, understands 99 languages, can translate them to English, and runs on your own computer, or even inside a web page.

| # | Project | What you'll have | Time |
|---|---------|------------------|------|
| 04 | [Transcribe a file with Whisper](04-transcribe-a-file-with-whisper) | any recording → text with timestamps, using OpenAI's own `whisper` package | 1 h |
| 05 | [Faster Whisper + live microphone](05-faster-whisper-live-microphone) | ~4× faster Whisper, transcribing as you speak | 1.5 h |
| 06 | [Subtitles for any video](06-subtitles-for-any-video) | a `.srt` subtitle file for any video or podcast | 1 h |
| 07 | [Whisper inside the browser](07-whisper-inside-the-browser) | speech-to-text with **no server at all** (transformers.js) | 1 h |
| 08 | [Any language → English](08-any-language-to-english) | detect the language and translate speech to English | 1 h |

**Install once** (in your activated venv; this downloads PyTorch, so give it a few minutes):
```bash
pip install openai-whisper faster-whisper "av<19" sounddevice soundfile numpy
```
- `openai-whisper`: OpenAI's Whisper (project 04). Careful: `pip install whisper` is a different, unrelated package.
- `faster-whisper`: the same models, faster (projects 05–08 and most of the course).
- `"av<19"`: the audio-decoding library faster-whisper uses; version 19 breaks faster-whisper 1.2, so we stay below it.
- **ffmpeg** must be installed too (see the [course setup](../README.md#setup-once)).

**Model sizes:** start with `base`. Bigger = more accurate but slower. Models download automatically the first time and are cached (openai-whisper: `~/.cache/whisper`; faster-whisper: `~/.cache/huggingface/hub`).

| Size | Download | Speed on a laptop CPU | When to use |
|------|----------|-----------------------|-------------|
| tiny | 75 MB | very fast | quick tests, weak computers |
| base | 140 MB | fast | **default for learning** |
| small | 480 MB | OK | good accuracy, other languages |
| medium | 1.5 GB | slow | high accuracy, translation |
| large-v3 / turbo | 1.6–3 GB | needs a GPU | best quality (`turbo` can't translate) |

Add `.en` (`tiny.en`, `base.en`...) for English-only versions that are a little more accurate in English.

Start here → [04 · Transcribe a file with Whisper](04-transcribe-a-file-with-whisper)
