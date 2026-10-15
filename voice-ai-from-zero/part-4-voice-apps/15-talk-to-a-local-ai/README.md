# 15 · Talk to a local AI

**What you'll build:** a spoken conversation with an AI that runs entirely on your computer. Press Enter, talk, press Enter: it answers out loud, and remembers what you said earlier in the conversation. Nothing goes to the internet.
**Like you're 10:** we connect three robots in a line: one that listens (Whisper), one that thinks (Llama), and one that talks (Kokoro).
**Time:** ~1.5 h · **Builds on:** [14 · Voice commands](../14-voice-commands), [11 · Kokoro](../../part-3-text-to-speech/11-studio-quality-voices-with-kokoro) · **Needs:** Ollama with `llama3.2:3b` (~2 GB), ~8 GB of RAM, a microphone and speakers

```
🎙️ you ──▶ Whisper (ears) ──▶ Llama 3.2 via Ollama (brain) ──▶ Kokoro (mouth) ──▶ 🔊
```

## Why this matters
This "ears → brain → mouth" chain (often called a **cascaded voice pipeline**, or STT → LLM → TTS) is how most voice assistants and AI phone agents are built today. Running it locally means private conversations and zero cost per minute. Every later project (16, 19, 22) is a variation of this file.

## What you'll learn
- **LLM (large language model)**: the "brain" that writes replies. Llama 3.2 3B has 3 billion parameters and runs on a laptop.
- **Ollama**: a free app that downloads and runs LLMs locally, and answers on `http://localhost:11434`.
- **Chat history (messages)**: the LLM has no memory; you send the whole conversation every time as a list of `system` / `user` / `assistant` messages.
- **System prompt**: the first message, with rules for the AI. Here: "your answer will be spoken, so keep it short and plain".
- **Latency**: total waiting time = Whisper time + LLM time + Kokoro time.

## Before you start
1. Install the Part 4 packages (skip if done):
   ```bash
   pip install faster-whisper "av<19" kokoro-onnx fastapi uvicorn python-multipart httpx pyttsx3 sounddevice soundfile numpy
   ```
   - `faster-whisper` (ears), `kokoro-onnx` (mouth), `httpx` (sends the conversation to Ollama), `sounddevice` + `numpy` (record and play).
2. Install **Ollama** from https://ollama.com/download and open it (on Linux the installer starts it as a service).
3. In a terminal, download the brain (once, ~2 GB):
   ```bash
   ollama pull llama3.2:3b
   ```
   Weaker computer (less than 8 GB RAM)? Use `ollama pull qwen2.5:1.5b` and change `MODEL = "qwen2.5:1.5b"` in `talk.py`.
4. Check it's running: open http://localhost:11434 in a browser. It should say **"Ollama is running"**.
5. No API key needed. Kokoro's files are reused from `voice-ai-from-zero/models/` (project 11), or downloaded there now (~340 MB).

## Run it
1. From the course folder:
   ```bash
   cd part-4-voice-apps/15-talk-to-a-local-ai
   python talk.py
   ```
2. Press **Enter**, ask a question out loud ("Why are foxes so fast?"), press **Enter** again.
3. Listen to the answer, then ask a follow-up ("And what do they eat?"). It remembers the topic.
4. Say "goodbye" to finish (or `Ctrl+C`).

### What you should see
```
🗣️  Say 'goodbye' to finish.

Press Enter, then speak...
🔴 Recording. Press Enter when you're done.
🧑 Why are foxes so fast?
🤖 Foxes are built for speed, with light bodies and long legs. They can run up to about 50 kilometres an hour when they need to escape or chase prey.

Press Enter, then speak...
🔴 Recording. Press Enter when you're done.
🧑 And what do they eat?
🤖 Foxes eat small animals like mice and rabbits, plus birds, insects, fruit and berries. They're not picky eaters.
```
The second question says only "they", yet the answer is about foxes: that's the chat history working. On a typical laptop each answer takes 3–10 seconds. Watch where the time goes: the 🧑 line appears fast (Whisper), the 🤖 line takes longest (the LLM), then Kokoro needs a moment before you hear it.

## How it works
Open `talk.py`.

1. **Setup.** Find (or download) Kokoro's files in the shared `models/` folder, exactly like project 11. Load `ears` (Whisper `base`) and `mouth` (Kokoro) once.
2. **`chat`** starts with one **system** message: "You are a friendly voice assistant... answer in 1-3 short sentences, with no lists, emojis or markdown." Without it, LLMs love bullet points and `**bold**`, which sound terrible read aloud.
3. **`record()`** waits for Enter, opens the microphone with `sd.InputStream(...)`, and the callback appends every chunk to `chunks` until you press Enter again (the `with` block ends, which closes the microphone). `np.concatenate(chunks)` joins them. This is **push-to-talk**: you decide when you're done, so no pause detection is needed.
4. **The loop** skips recordings shorter than half a second, then transcribes with `vad_filter=True`. Empty result → "(I didn't catch that)".
5. **`think(text)`** appends your words as a `user` message and sends the *whole* `chat` list to Ollama's `/api/chat` with `httpx.post(...)`. `"stream": False` means "send the full answer at once". `timeout=120` waits up to 2 minutes (the first answer is slow because Ollama loads the model into memory). The reply is in `data["message"]["content"]`; we append it as an `assistant` message so the next question has the full context. If Ollama isn't running (`httpx.ConnectError`) or the model isn't downloaded (`"error"` in the answer), the program stops with a clear message.
6. **`speak(text)`** makes audio with Kokoro (`speed=1.1`, slightly faster than normal, which sounds natural for an assistant) and plays it.
7. If you said "goodbye", the loop ends after the answer.

What Ollama receives on your second question:
```json
{"model": "llama3.2:3b", "stream": false, "messages": [
  {"role": "system", "content": "You are a friendly voice assistant..."},
  {"role": "user", "content": "Why are foxes so fast?"},
  {"role": "assistant", "content": "Foxes are built for speed..."},
  {"role": "user", "content": "And what do they eat?"}]}
```

## If something goes wrong
- **`Can't reach Ollama...`** → Ollama isn't running. Open the Ollama app (Windows/Mac) or run `ollama serve` in another terminal (Linux), then check http://localhost:11434.
- **`Ollama says: model 'llama3.2:3b' not found`** → run `ollama pull llama3.2:3b` (or change `MODEL` to a model you have; `ollama list` shows them).
- **The first answer takes very long, or `httpx.ReadTimeout`** → Ollama is loading the 2 GB model into memory. Wait and try again; later answers are faster. If it's always slow, use `qwen2.5:1.5b`.
- **`(That was too short. Try again.)` every time** → you pressed Enter twice too quickly. Press Enter, *then* speak, *then* press Enter.
- **It answers in long lists anyway** → small models sometimes ignore the system prompt. Make the instruction stronger ("Never use lists.") or try another model.

## Try this
1. **Easy:** give it a personality in the system message: a pirate, or a Spanish teacher who corrects your mistakes.
   <details><summary>Hint</summary>Edit the text in the first <code>chat</code> message, e.g. <code>"You are a patient Spanish teacher. The user practises Spanish. Reply in simple Spanish, then correct their mistakes in one short English sentence."</code> Keep the "spoken aloud, 1-3 short sentences" part. For Spanish speech, also use a Spanish Kokoro voice: <code>VOICE = "ef_dora"</code> and <code>lang="es"</code> in <code>speak()</code>.</details>
2. **Medium:** print how long each step takes, to find the slowest one.
   <details><summary>Solution</summary>

   Add `import time` at the top, then in the loop:
   ```python
   t0 = time.time()
   segments, _ = ears.transcribe(audio, vad_filter=True)
   heard = " ".join(s.text.strip() for s in segments)
   t1 = time.time()
   # ... (keep the checks and print) ...
   reply = think(heard)
   t2 = time.time()
   print("🤖", reply)
   speak(reply)
   print(f"⏱ ears {t1 - t0:.1f}s · brain {t2 - t1:.1f}s · mouth+playback {time.time() - t2:.1f}s")
   ```
   Usually the brain is the slowest. Project 19 hides that wait by streaming.
   </details>
3. **Harder:** swap Kokoro for Piper (project 10) and compare speed and quality.
   <details><summary>Hint</summary>Copy <code>en_US-lessac-medium.onnx</code> and <code>.onnx.json</code> from project 10 into this folder. Load it with <code>from piper import PiperVoice</code> and <code>mouth = PiperVoice.load("en_US-lessac-medium.onnx")</code>. In <code>speak()</code>, join the audio Piper yields: <code>samples = np.concatenate([c.audio_float_array for c in mouth.synthesize(text)])</code>, and play it at <code>mouth.config.sample_rate</code>.</details>

## Check yourself
1. Why must the program send the whole conversation to Ollama every time?
2. What is the system message for, and why does it matter more for voice than for text chat?
3. Which of the three steps is usually the slowest, and how could you hide that delay?
4. What happens on the 30th question if the conversation keeps growing? (Think about what is sent each time.)

<details><summary>Answers</summary>

1. The LLM has no memory between requests; it only knows what's in the messages you send.
2. It sets rules for every answer. For voice, answers must be short and free of markdown, lists and emojis, which can't be spoken naturally.
3. The LLM. You can stream its answer and start speaking the first sentence while it writes the rest (project 19).
4. Each request gets longer, so answers get slower, and eventually the conversation no longer fits in the model's context window. Real apps keep only the last N messages (project 16 sends the last 10).
</details>

## Learn more (optional)
- Ollama on GitHub (API docs in `docs/api.md`): https://github.com/ollama/ollama
- Ollama model library: https://ollama.com/library
- Search YouTube for "build a local voice assistant whisper ollama".

## Next
→ [16 · Voice assistant web app](../16-voice-assistant-web-app)
