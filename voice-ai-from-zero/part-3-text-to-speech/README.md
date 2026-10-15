# Part 3 · Text to speech

Now your computer talks back, from robotic to remarkably human, all offline.

| # | Project | Voice quality | What you'll have | Time |
|---|---------|---------------|------------------|------|
| 09 | [Your computer speaks](09-your-computer-speaks) | 🤖 robotic | instant speech with the voices built into your computer | 45 min |
| 10 | [Natural voices with Piper](10-natural-voices-with-piper) | 🙂 natural | a fast neural voice, 40+ languages, faster than real time | 1 h |
| 11 | [Studio-quality voices with Kokoro](11-studio-quality-voices-with-kokoro) | 😍 very natural | 50+ voices you can even mix together | 1 h |
| 12 | [Speech in the browser](12-speech-in-the-browser) | 🤖 → 😍 | the browser's own voices, then Kokoro running inside the page | 1 h |

**Install once** (in your activated venv):
```bash
pip install pyttsx3 piper-tts kokoro-onnx soundfile sounddevice numpy
```
- `pyttsx3`: system voices (09) · `piper-tts`: Piper (10) · `kokoro-onnx`: Kokoro (11, and later projects) · `soundfile`, `sounddevice`, `numpy`: save, play, handle audio.
- **Linux only:** `sudo apt install espeak-ng` for project 09.

**Downloads:** Piper voices (~60 MB each) go into project 10's folder. Kokoro's two files (~340 MB) are downloaded once into **`voice-ai-from-zero/models/`** and shared by every later project that speaks, so you only download them once.

Start here → [09 · Your computer speaks](09-your-computer-speaks)
