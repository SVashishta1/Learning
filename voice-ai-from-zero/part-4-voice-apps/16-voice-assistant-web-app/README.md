# 16 · Voice assistant web app

**What it does:** project 15 as a web page. Hold the green button, speak, let go: your words and the answer appear as chat bubbles and the answer is spoken. Pick the voice from a menu.

## Run it
```bash
cd part-4-voice-apps/16-voice-assistant-web-app
uvicorn server:app
```
Open http://localhost:8000. (Copy the Kokoro files from project 11 into this folder to skip the download.)

## How it fits together
```
browser: hold button → MediaRecorder → POST /talk (audio + chat history + voice)
server:  Whisper → Ollama → Kokoro → JSON {heard, reply, audio}
browser: shows bubbles, plays the audio
```
The **browser keeps the chat history**, so the server remembers nothing between requests. That makes it simple, and several people could use it at once.

## Try this
1. Show how long each step took: time them in `talk()` with `time.time()` and display it. Which step is slowest?
2. Add a "🔁 replay" button on each bot bubble.
3. Combine with project 07: do the Whisper step **in the browser**, and send only text to the server.
