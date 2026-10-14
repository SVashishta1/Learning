# Part 4 · Voice apps

Now we join the pieces: **ears** (Whisper) + **brain** (a local LLM) + **mouth** (Kokoro) = real apps.

| # | Project | What you'll have |
|---|---------|------------------|
| 13 | [Voice notes app](13-voice-notes-app) | record notes in the browser; they're written down and searchable |
| 14 | [Voice commands](14-voice-commands) | say "open YouTube", "timer 2 minutes", "what time is it" |
| 15 | [Talk to a local AI](15-talk-to-a-local-ai) | a spoken conversation with an LLM on your own computer |
| 16 | [Voice assistant web app](16-voice-assistant-web-app) | hold-to-talk assistant in the browser, like a mini Siri |

Install once:
```bash
pip install faster-whisper "av<19" kokoro-onnx fastapi uvicorn python-multipart httpx pyttsx3 sounddevice soundfile numpy
```

**The local "brain" (projects 15, 16 and Part 5):**
1. Install **Ollama** from https://ollama.com/download
2. In a terminal: `ollama pull llama3.2:3b` (about 2 GB, once). Weaker computer? `ollama pull qwen2.5:1.5b` and change `MODEL` in the code.
3. Ollama runs in the background. Check: open http://localhost:11434, it should say "Ollama is running".
