# 19 · Real-time assistant with interruptions

**What you'll build:** a voice assistant that feels like a phone call. No buttons: just talk. It starts answering shortly after you stop, speaks its answer sentence by sentence, and if you talk over it, it **stops immediately and listens** (this is called **barge-in**).
**Like you're 10:** instead of sending letters back and forth (record, send, wait, reply), the browser and the server keep a phone line open, so sound flows both ways all the time.
**Time:** ~3 h · **Builds on:** [18 · Who spoke when](../18-who-spoke-when), the VAD from [17](../17-hands-free-with-voice-detection) and the assistant from [16](../../part-4-voice-apps/16-voice-assistant-web-app) · **Needs:** Ollama with `llama3.2:3b`, Chrome or Edge, **headphones**

## Why this matters
"Latency" and "interruptions" are what separate a demo from a voice product people enjoy using. Commercial voice agents (customer-service bots, ChatGPT's voice mode, AI receptionists) are built on exactly these ideas: stream audio over a WebSocket, detect the end of the user's turn with a VAD, stream the LLM's answer, speak the first sentence while the next is still being written, and cancel everything when the user interrupts. You'll build all five, locally.

## What you'll learn
- **WebSocket**: a connection that stays open, so both sides can send messages whenever they like (unlike normal HTTP requests).
- **Streaming**: handing over pieces as soon as they're ready (microphone chunks, LLM words, spoken sentences) instead of everything at the end.
- **Turn detection**: deciding the user has finished, here with Silero VAD and 0.5 s of silence.
- **Barge-in**: interrupting the bot; the server cancels its work (`reply.cancel()`) and the browser stops playing.
- **async / await and tasks**: how one Python server listens to your microphone *and* generates an answer at the same time.

## Before you start
1. Packages: Part 4's line plus Part 5's (skip what you have):
   ```bash
   pip install faster-whisper "av<19" kokoro-onnx fastapi uvicorn python-multipart httpx soundfile numpy
   pip install silero-vad jiwer scipy websockets
   ```
   - `fastapi` + `uvicorn` + `websockets`: the server. Plain `uvicorn` can't do WebSockets by itself; the `websockets` package adds that.
   - `silero-vad` (+ PyTorch): detects when you start and stop talking.
   - `faster-whisper` (ears), `httpx` (streams from Ollama), `kokoro-onnx` + `soundfile` (mouth).
2. Ollama running with `ollama pull llama3.2:3b` done (see [project 15](../../part-4-voice-apps/15-talk-to-a-local-ai)).
3. **Headphones.** Without them the microphone hears the assistant, thinks you're talking, and it interrupts itself.
4. No API key needed. Kokoro's files come from `voice-ai-from-zero/models/` (downloaded there if missing).

## Run it
1. From the course folder:
   ```bash
   cd part-5-advanced/19-real-time-assistant-with-interruptions
   uvicorn server:app
   ```
2. Open http://localhost:8000 in **Chrome or Edge**, put on headphones, click **Start conversation**, allow the microphone.
3. Ask something ("Tell me something about foxes."), then just wait: no button.
4. While it's answering, interrupt it: "Wait, stop. What do they eat?" It goes quiet straight away and answers the new question.

### What you should see
The chat on the page (from our test, where we interrupted after the second sentence):
```
                                                       Tell me something about Foxes.
Foxes are clever wild dogs that live on every continent except Antarctica.
They have excellent hearing and can hear a mouse squeak from far away.
                                                         Wait stop what do they eat?
Foxes mostly eat mice, rabbits, birds and insects, plus fruit and berries.
```
The bot's text grows one sentence at a time, and you hear each sentence as soon as its text appears. The first answer would have had four sentences; the interruption cut it after two.

The terminal only shows the connection:
```
INFO:     127.0.0.1:35066 - "WebSocket /ws" [accepted]
INFO:     connection open
```
On a typical laptop the first sentence starts about 1–3 s after you stop talking (our slow test machine took much longer, because it makes speech slower than real time). Project 16 always waited for the *whole* answer.

## How it works
Project 16 waits for every step to finish: record → transcribe → whole answer → whole audio. Here everything **streams**:
```
browser mic ──32 ms chunks──▶ WebSocket ──▶ Silero VAD: "you stopped talking"
                                             │
                                             ▼
                    Whisper ──▶ Ollama streams words ──▶ each full sentence ──▶ Kokoro ──▶ WAV ──▶ browser plays it
                                                          (sentence 2 is written while sentence 1 plays)
```
**Messages on the WebSocket**: browser → server: raw audio (512 numbers at a time). Server → browser: `{"type": "you"}` (what you said), `{"type": "bot"}` (one sentence of text), a WAV file (that sentence spoken), `{"type": "stop"}` (be quiet) and `{"type": "error"}`.

**`index.html`** (the browser)
1. **Start** opens `new WebSocket("ws://localhost:8000/ws")`.
2. **Microphone → 16 kHz numbers.** `new AudioContext({ sampleRate: 16000 })` makes the browser convert the microphone to 16 kHz. An **AudioWorklet** (a tiny program on the browser's audio thread) receives every block of 128 samples and posts it to the page. `echoCancellation: true` asks the browser to remove the assistant's voice from the mic (headphones are still better).
3. **Send exactly 512 at a time.** 128-sample blocks are collected in `buffer`; every time there are 512 (32 ms, what Silero needs), `ws.send(...)` sends them.
4. **Receiving.** A `Blob` is a WAV: it goes into `audioQueue`, and `playNext()` plays them one after another. Text messages add bubbles. `"stop"` calls `stopTalking()`: empty the queue, pause the current sentence, and ignore any WAV still on its way until your next question appears (`"you"`).

**`server.py`** (the server)
5. **`conversation(ws)`** runs once per browser connection. It creates a VAD (`min_silence_duration_ms=500`: half a second of silence = your turn is over) and the chat history, then loops forever: receive 512 samples, `np.frombuffer(..., dtype=np.float32)` turns the bytes back into numbers, ask the VAD.
   - VAD **start** → you're talking. If an answer is still running, `reply.cancel()` stops it, and `{"type": "stop"}` tells the browser to go quiet. That's barge-in.
   - VAD **end** → your speech is added to `question`, and `asyncio.create_task(answer(...))` starts answering *in the background* while the loop keeps listening.
6. **`answer(ws, question, chat)`** transcribes (in a helper thread with `asyncio.to_thread`, so the loop isn't frozen), then clears `question`. If you pause briefly and keep talking *before* it has understood you, the new start cancels the task and both parts stay in `question`, so they're answered as one question.
7. **`sentences(chat)`** streams from Ollama (`"stream": True`, `client.stream(...)`, `aiter_lines()`): each line is a small JSON with a few new words. They're added to `text`, and `re.split(r"(?<=[.!?])\s+", text)` cuts after `.`, `!` or `?` followed by a space. Every finished sentence is `yield`ed immediately; the unfinished end is kept for later.
8. For each sentence, `answer()` makes a WAV with Kokoro (`to_wav`, in a helper thread), sends the text, then the audio. `finally:` saves whatever was actually said into the chat history, even when interrupted, so the LLM knows where it was cut off.
9. Errors from Ollama (not running, model missing) are sent to the page as `{"type": "error"}`.

## If something goes wrong
- **It interrupts itself, or answers its own words** → wear headphones. Echo cancellation in browsers isn't perfect.
- **Nothing happens after you speak** → check Ollama is running (the page shows `❌ Can't reach Ollama...` if not). Then check the microphone: the page must say "🎧 listening...".
- **Firefox: `Connecting AudioNodes from AudioContexts with different sample-rate is currently not supported`** → use Chrome or Edge; Firefox can't resample the microphone this way.
- **It cuts you off while you're thinking** → raise `min_silence_duration_ms=500` in `server.py` to `800`. Short pauses are fine: if it hasn't understood you yet, your next words are joined to the question.
- **Terminal: `WARNING: No supported WebSocket library detected`, and the page says "Disconnected"** → `pip install websockets`, then restart uvicorn.
- **"Disconnected. Reload the page to start again."** → the server stopped or crashed. Look at the terminal for the error, fix it, restart `uvicorn server:app`, and reload.

## Try this
1. **Easy:** make it snappier or more patient: set `min_silence_duration_ms` to 300, then to 900. How does each feel?
   <details><summary>Hint</summary>It's in <code>conversation()</code> in <code>server.py</code>. Restart uvicorn after each change. 300 answers quickly but jumps in when you pause to think; 900 feels polite but slow. Real products tune this carefully, and some use a small model that predicts whether your sentence is finished.</details>
2. **Medium:** measure your **latency**: the time from the end of your speech to the first WAV being sent.
   <details><summary>Solution</summary>

   In `server.py`, add `import time`. In `conversation()`, pass the time when your speech ended: `asyncio.create_task(answer(ws, question, chat, time.time()))`. Change `answer`'s first line to `async def answer(ws, question, chat, ended):`, and after `await ws.send_bytes(wav)` add:
   ```python
   if len(said) == 0:
       print(f"⏱ latency: {time.time() - ended:.2f} s")
   ```
   (It's before `said.append(sentence)`, so it only prints for the first sentence.) Good products aim for under 1 second.
   </details>
3. **Harder:** use a faster brain and compare latency: `ollama pull qwen2.5:1.5b`, set `MODEL = "qwen2.5:1.5b"`.
   <details><summary>Hint</summary>Use exercise 2 to measure both models with the same question. Smaller models start answering sooner but say sillier things. You can also try a faster voice: Piper (project 10) makes audio much faster than Kokoro on a CPU.</details>

## Check yourself
1. Why does this project use a WebSocket instead of a normal `POST` request like project 16?
2. What two things happen when you start talking while the bot is speaking?
3. Why is the LLM's answer split into sentences before going to Kokoro?
4. Why does `answer()` run as a separate task (`asyncio.create_task`) instead of being called directly in the loop?

<details><summary>Answers</summary>

1. Audio has to flow continuously in both directions (your microphone up, the bot's sentences down) and the server must be able to say "stop" at any moment. A WebSocket stays open for that; a POST is one request and one reply.
2. The server cancels the answer task (no more words or audio are made) and sends `{"type": "stop"}`; the browser pauses the current audio and throws away queued sentences.
3. So it can start speaking the first sentence while the LLM is still writing the rest. That hides most of the LLM's thinking time.
4. The loop must keep receiving microphone chunks and running the VAD while the answer is made, otherwise it couldn't notice you interrupting.
</details>

## Learn more (optional)
- FastAPI WebSockets: https://fastapi.tiangolo.com/advanced/websockets/
- MDN, AudioWorklet: https://developer.mozilla.org/en-US/docs/Web/API/AudioWorklet
- Python `asyncio` tasks: https://docs.python.org/3/library/asyncio-task.html
- Search YouTube for "voice agent latency" or "how voice AI agents handle interruptions".

## Next
→ [20 · Clone your own voice](../20-clone-your-own-voice)
