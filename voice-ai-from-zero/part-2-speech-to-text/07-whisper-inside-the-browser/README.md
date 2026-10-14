# 07 · Whisper inside the browser

**What it does:** a web page that runs Whisper **inside your browser**. Record or pick a file and get a transcript with **no server, no Python and no upload**: the model downloads once and runs on your device (on the graphics card via WebGPU when available).

## Run it
```bash
cd part-2-speech-to-text/07-whisper-inside-the-browser
python -m http.server 8000
```
Open http://localhost:8000 in **Chrome or Edge**, pick a model, then **Record** or **Pick an audio file**. The first run downloads the model (40–250 MB); after that it's cached.

## The idea in one sentence
**transformers.js** runs the same Hugging Face models in JavaScript, so a whole AI feature can live in one HTML file: private (audio never leaves the device) and free to host.

## Try this
1. Compare `tiny.en` vs `base` on the same recording: speed vs accuracy.
2. Open the page on your phone over Wi-Fi (`python -m http.server 8000 --bind 0.0.0.0`). Note that browsers only allow the microphone on `localhost` or `https`, so use the file picker there.
3. Change the `pipeline(...)` line to add `return_timestamps: true` and show the times.

## Read
- transformers.js docs: https://huggingface.co/docs/transformers.js
