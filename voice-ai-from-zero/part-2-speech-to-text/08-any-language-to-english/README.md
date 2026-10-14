# 08 · Any language → English

**What it does:** detects which of 99 languages is spoken, writes it down in that language, and translates it to English, all offline.

## Run it
```bash
cd part-2-speech-to-text/08-any-language-to-english
python translate_speech.py some_clip_in_another_language.mp3
```
No clip? Record yourself (project 01) in any language you know, or download a short news clip in another language.

## The idea in one sentence
The same Whisper model can either **transcribe** (same language) or **translate** (to English) just by changing `task=`.

## Try this
1. Combine it with project 06 to make English subtitles for a foreign film.
2. Try a language mix ("Hinglish", "Spanglish"). What does it detect?
