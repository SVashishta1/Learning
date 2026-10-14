# 15 · Talk to a local AI

**What it does:** a spoken conversation with an AI. Press Enter, talk, press Enter: it answers out loud. Nothing goes to the internet.

```
🎙️ you ──▶ Whisper (ears) ──▶ Llama 3.2 via Ollama (brain) ──▶ Kokoro (mouth) ──▶ 🔊
```

## Run it
1. Ollama installed and `ollama pull llama3.2:3b` done (see the Part 4 README).
2. ```bash
   cd part-4-voice-apps/15-talk-to-a-local-ai
   python talk.py
   ```
The first run downloads the Kokoro files (~350 MB). Copy them from project 11 to skip that.

## Things to notice
- The **system message** tells the LLM its answer will be *spoken*: short, no markdown. Try removing it and hear how bad bullet points sound read aloud.
- `chat` keeps the whole conversation, so you can ask follow-ups ("and why is that?").
- The total wait = Whisper time + LLM time + Kokoro time. Project 19 makes it feel instant by **streaming** each step.

## Try this
1. Give it a personality in the system message (a pirate, a Spanish teacher who corrects your mistakes...).
2. Try other voices (`bm_george`, `af_bella`) and `speed=1.3`.
3. Swap Kokoro for Piper (project 10) and compare speed.
