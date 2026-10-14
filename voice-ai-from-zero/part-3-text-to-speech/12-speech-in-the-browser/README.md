# 12 · Speech in the browser

**What it does:** one web page with two kinds of voices:
- **A.** The browser's **built-in voices** (`speechSynthesis`): instant, zero download.
- **B.** **Kokoro running inside the page** (`kokoro-js`): a real neural voice, downloaded once and then fully on your device.

## Run it
```bash
cd part-3-text-to-speech/12-speech-in-the-browser
python -m http.server 8000
```
Open http://localhost:8000 in Chrome or Edge. Type something and try both buttons.

## The idea in one sentence
The browser can both **listen** (Whisper in project 07) and **speak** (Kokoro here) with no server, so complete voice apps can run privately in a single web page.

## Try this
1. Change `device: "wasm"` to `"webgpu"` (and `dtype: "fp32"`). Is it faster on your machine?
2. Add a speed slider: `tts.generate(text, { voice, speed: 1.2 })`.
