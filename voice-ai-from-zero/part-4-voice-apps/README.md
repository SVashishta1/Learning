# Part 4 · Voice apps

Now we join the pieces: **ears** (Whisper) + **brain** (a local LLM) + **mouth** (Kokoro) = real apps.

| # | Project | What you'll have | Time |
|---|---------|------------------|------|
| 13 | [Voice notes app](13-voice-notes-app) | record notes in the browser; they're written down, saved in SQLite and searchable | 2 h |
| 14 | [Voice commands](14-voice-commands) | say "open YouTube", "set a timer for 2 minutes", "what time is it" | 1.5 h |
| 15 | [Talk to a local AI](15-talk-to-a-local-ai) | a spoken conversation with an LLM on your own computer | 1.5 h |
| 16 | [Voice assistant web app](16-voice-assistant-web-app) | hold-to-talk assistant in the browser, like a mini Siri | 2 h |

**Install once** (in your activated venv):
```bash
pip install faster-whisper "av<19" kokoro-onnx fastapi uvicorn python-multipart httpx pyttsx3 sounddevice soundfile numpy
```
- `faster-whisper` + `"av<19"`: ears · `kokoro-onnx`: mouth · `httpx`: talks to Ollama.
- `fastapi`, `uvicorn`, `python-multipart`: web servers and file uploads (13, 16).
- `pyttsx3`: quick system voice for project 14 (Linux: `sudo apt install espeak-ng`).

**The local "brain" (projects 15, 16 and Part 5):**
1. Install **Ollama** from https://ollama.com/download and open it.
2. In a terminal: `ollama pull llama3.2:3b` (about 2 GB, once). Weaker computer (under 8 GB RAM)? `ollama pull qwen2.5:1.5b` and change `MODEL` in the code.
3. Ollama runs in the background. Check: open http://localhost:11434; it should say "Ollama is running".

**Web apps (13, 16):** run them with `uvicorn server:app` from inside the project folder, then open http://localhost:8000. Only one can use port 8000 at a time: stop one (`Ctrl+C`) before starting another.

Start here → [13 · Voice notes app](13-voice-notes-app)
