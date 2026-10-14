# 19 · Real-time assistant with interruptions

**What it does:** a voice assistant that feels like a phone call. No buttons: just talk. It starts answering about a second after you stop, and if you talk over it, it **stops and listens** (this is called *barge-in*).

## Run it
```bash
cd part-5-advanced/19-real-time-assistant-with-interruptions
uvicorn server:app
```
Open http://localhost:8000 in **Chrome or Edge**, put on **headphones** (otherwise it hears itself and interrupts itself), press *Start*.

## Why it feels fast
Project 16 waits for every step to finish: record → transcribe → whole answer → whole audio. Here everything **streams**:

```
browser mic ──32 ms chunks──▶ WebSocket ──▶ Silero VAD: "you stopped talking"
                                             │
                                             ▼
                    Whisper ──▶ Ollama streams words ──▶ each full sentence ──▶ Kokoro ──▶ WAV ──▶ browser plays it
                                                          (sentence 2 is written while sentence 1 plays)
```
**Interrupting:** when the VAD hears you start talking, the server cancels the answer (`reply.cancel()`) and sends `{"type": "stop"}`; the browser stops the audio and throws away queued sentences.

## Words you'll hear in the industry
- **Latency**: time from you finishing to the bot starting. Good: under 1 s. Measure yours!
- **Streaming**: handing over pieces as soon as they're ready, instead of the whole thing at the end.
- **Barge-in**: interrupting the bot.
- **Turn detection**: deciding when the user has finished (here: 0.5 s of silence).

## Try this
1. Print the latency: record `time.time()` at the VAD "end" event and when the first WAV is sent.
2. Change `min_silence_duration_ms` to 300 (snappier, but cuts you off) and 900 (patient).
3. Use a faster brain: `ollama pull qwen2.5:1.5b`. How much does latency drop?
