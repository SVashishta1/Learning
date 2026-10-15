# 16 · Voice assistant web app

**What you'll build:** project 15 as a web page, like a mini Siri. Hold the green button, speak, let go: your words and the answer appear as chat bubbles, and the answer is spoken in the voice you pick from a menu.
**Like you're 10:** the web page is the walkie-talkie; the Python server is the clever friend at the other end who listens, thinks and answers.
**Time:** ~2 h · **Builds on:** [15 · Talk to a local AI](../15-talk-to-a-local-ai) and the web app pattern from [13](../13-voice-notes-app) · **Needs:** Ollama running with `llama3.2:3b`, a microphone, a browser

## Why this matters
Most people will use your voice AI through a web page or app, not a terminal. This project splits the work the way real products do: the **browser** handles the microphone, buttons and playback; the **server** runs the heavy AI models. Because the page can also run on a phone on the same Wi-Fi, this is the first thing you've built that friends can try.

## What you'll learn
- **Hold-to-talk (push-to-talk)**: start recording on `pointerdown`, stop on `pointerup`, a reliable way to know when the user has finished.
- **Stateless server**: the server remembers nothing between requests; the **browser keeps the chat history** and sends it each time.
- **Sending audio back as base64**: binary audio turned into text so it fits inside a JSON answer.
- **HTTP status codes**: `200` = OK, `503` = a service we depend on (Ollama) is unavailable, `500` = something failed on the server.

## Before you start
1. Install the Part 4 packages (skip if done):
   ```bash
   pip install faster-whisper "av<19" kokoro-onnx fastapi uvicorn python-multipart httpx pyttsx3 sounddevice soundfile numpy
   ```
   - `fastapi` + `uvicorn` + `python-multipart`: the web server and file uploads.
   - `faster-whisper` (ears), `httpx` (talks to Ollama), `kokoro-onnx` + `soundfile` (mouth, and turning the audio into a WAV).
2. Ollama installed and running, with `ollama pull llama3.2:3b` done (see [project 15](../15-talk-to-a-local-ai) or the Part 4 README). Check http://localhost:11434 says "Ollama is running".
3. No API key needed. Kokoro's files are reused from `voice-ai-from-zero/models/` (downloaded there if missing, ~340 MB).

## Run it
1. From the course folder:
   ```bash
   cd part-4-voice-apps/16-voice-assistant-web-app
   uvicorn server:app
   ```
2. Wait for `Application startup complete` (loading Whisper and Kokoro takes a few seconds), then open http://localhost:8000.
3. The first time, press the button once to allow the microphone.
4. **Hold** the green button, ask something, **release**. Try a follow-up question, then change the **Voice** menu and ask again.

### What you should see
In the terminal, one line per question:
```
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     127.0.0.1:52144 - "GET / HTTP/1.1" 200 OK
INFO:     127.0.0.1:52144 - "POST /talk HTTP/1.1" 200 OK
INFO:     127.0.0.1:52144 - "POST /talk HTTP/1.1" 200 OK
```
On the page: while you hold, the button turns red and says "Listening... (release to send)". After you release, the status shows "🤔 thinking...", then two bubbles appear (yours on the right in blue, the assistant's on the left in grey) and the answer plays:
```
                         The quick brown fox jumps over the lazy dog. Machine learning is fun.
Foxes are fast and clever. They can run up to fifty kilometres an hour! Anything else?
```
If Ollama isn't running, the status says `❌ Can't reach Ollama. Start the Ollama app and try again.` and the terminal shows `"POST /talk HTTP/1.1" 503 Service Unavailable`.

## How it works
```
browser: hold button → MediaRecorder → POST /talk (audio + chat history + voice)
server:  Whisper → Ollama → Kokoro → JSON {heard, reply, audio}
browser: shows bubbles, saves history, plays the audio
```

**`server.py`** (one route does everything)
1. **Start-up**: get Kokoro's files (shared `models/` folder), load `ears` and `mouth` once.
2. **`talk(audio, history, voice)`** receives three things from the form: the recording (`UploadFile`), the history as a JSON string (`Form("[]")` = default empty list) and the voice name. It's a plain `def`, so FastAPI runs it in a helper thread and the server stays responsive while the AI works.
3. **Ears**: `ears.transcribe(io.BytesIO(...))`. Nothing heard → return empty fields and the page says "I didn't catch that".
4. **Brain**: build `messages` = system prompt + `json.loads(history)` (the browser's copy of the conversation) + your new words, and send them to Ollama with `httpx.post(...)`. If Ollama can't be reached, `raise HTTPException(503, ...)` sends a clear error to the page instead of crashing.
5. **Mouth**: `mouth.create(reply, voice=voice, ...)` makes the audio; `sf.write(wav, samples, rate, format="WAV")` writes a WAV file into memory (`io.BytesIO`), and `base64.b64encode(...)` turns its bytes into plain text so it fits in the JSON answer.

**`index.html`**
6. **`onpointerdown`** (works for mouse and touch) sets `holding = true`, asks for the microphone, and starts a `MediaRecorder`. If you already let go while the browser was asking for permission (`!holding`), it releases the microphone and tells you to press again; otherwise a recording would start that never stops.
7. **`onpointerup` / `onpointerleave`** stop the recorder. Its `onstop` releases the microphone and calls `send()`.
8. **`send()`** skips tiny recordings (an accidental tap), then posts a `FormData` with the audio, `history.slice(-10)` (only the last 10 messages, so requests stay small and fast) and the chosen voice. If the answer isn't OK, it shows `data.detail` (FastAPI's error message).
9. On success, `show(...)` adds the two bubbles (with `textContent`, so text is never run as HTML), both messages are pushed onto `history`, and `new Audio("data:audio/wav;base64," + data.audio).play()` plays the WAV straight from the text.

## If something goes wrong
- **"❌ Can't reach Ollama"** → start the Ollama app (or `ollama serve`) and check http://localhost:11434.
- **"❌ Ollama says: model 'llama3.2:3b' not found"** → `ollama pull llama3.2:3b`.
- **The button stays red / "Microphone ready. Now hold the button..."** → the first press only asks for permission. Allow it, then hold the button again.
- **"I didn't catch that." every time** → you released too early (hold until you've finished the sentence), or the browser uses the wrong microphone (🔒 icon → site settings).
- **It works on your computer but the microphone fails on your phone** → browsers only allow the microphone on `localhost` or `https://`. Opening `http://192.168.x.x:8000` from a phone is "not secure", so the microphone is blocked. (Tools like `ngrok` or `cloudflared` give you an `https://` address if you want to try.)

## Try this
1. **Easy:** add two more voices to the menu, for example `am_michael` and `bf_isabella`.
   <details><summary>Hint</summary>Add <code>&lt;option&gt;am_michael&lt;/option&gt;&lt;option&gt;bf_isabella&lt;/option&gt;</code> inside the <code>&lt;select id="voice"&gt;</code>. Any of Kokoro's English voice names from project 11 works.</details>
2. **Medium:** show how long each step took (ears, brain, mouth) under the bot bubble. Which step is slowest?
   <details><summary>Solution</summary>

   In `server.py`, add `import time`, then put `t0 = time.time()` at the start of `talk`, `t1 = time.time()` after the transcribe line, `t2 = time.time()` after `reply = ...`, and return an extra field:
   ```python
   "timing": f"ears {t1 - t0:.1f}s · brain {t2 - t1:.1f}s · mouth {time.time() - t2:.1f}s",
   ```
   In `index.html`, after `show(data.reply, "bot");` add `status.textContent = data.timing;`.
   </details>
3. **Harder:** add a "🔁 replay" button on each bot bubble that plays its answer again.
   <details><summary>Hint</summary>Change <code>show()</code> so it returns the <code>div</code>. After <code>const bubble = show(data.reply, "bot");</code>, create the audio once (<code>const sound = new Audio("data:audio/wav;base64," + data.audio);</code>), then add a button: <code>const b = document.createElement("button"); b.textContent = "🔁"; b.onclick = () => sound.play(); bubble.appendChild(b);</code> and call <code>sound.play()</code>.</details>

## Check yourself
1. Where is the conversation history stored, and why is that convenient for the server?
2. Why does the server send audio as base64 text?
3. What would go wrong without the `holding` check in `onpointerdown`?
4. Why does `send()` only send the last 10 messages?

<details><summary>Answers</summary>

1. In the browser (`history` in `index.html`), sent with every request. The server stays simple and stateless: it doesn't need to track users, and several people can use it at once.
2. JSON can only contain text. Base64 turns any bytes into letters and digits, so the WAV fits inside the JSON together with the text answer.
3. On the first use, the permission pop-up appears while you hold the button. You let go to click "Allow", so the "stop" event happens before recording starts, and the recording would never stop.
4. Each request includes the history, so a long history makes requests bigger and the LLM slower, and could exceed the model's context window. The last 10 messages keep enough context for follow-up questions.
</details>

## Learn more (optional)
- FastAPI request forms and files: https://fastapi.tiangolo.com/tutorial/request-forms-and-files/
- MDN, Pointer events: https://developer.mozilla.org/en-US/docs/Web/API/Pointer_events
- Search YouTube for "push to talk web app javascript MediaRecorder".

## Next
→ [Part 5 · 17 · Hands-free with voice detection](../../part-5-advanced/17-hands-free-with-voice-detection)
