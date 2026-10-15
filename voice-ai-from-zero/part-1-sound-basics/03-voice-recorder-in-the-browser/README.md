# 03 · Voice recorder in the browser

**What you'll build:** a web page that records your voice, shows a live volume meter while you talk, and lists your recordings so you can play or download them. One HTML file, no Python code.
**Like you're 10:** your web browser already has a microphone, a tape recorder and a volume meter built in. We just add three buttons' worth of code.
**Time:** ~1 h · **Builds on:** [02 · See your voice](../02-see-your-voice) · **Needs:** Chrome, Edge, Firefox or Safari, and a microphone

## Why this matters
Most voice apps people use run in a browser or phone app, not a terminal. The browser pieces you meet here (`getUserMedia`, `MediaRecorder`, `AudioContext`) are the same ones behind Google Meet, voice notes in web apps, and the voice assistants you'll build in projects 13, 16, 19 and 22. In project 07 you'll even run Whisper on this page.

## What you'll learn
- **`getUserMedia`**: the browser function that asks permission and gives you the microphone as a live **stream**.
- **`MediaRecorder`**: the browser's built-in recorder. It turns the stream into a compressed audio file (usually `.webm`).
- **`AnalyserNode`**: a part of the **Web Audio API** that lets you read the sound's numbers while it plays, so you can draw a meter.
- **Secure context**: browsers only allow the microphone on `https://` pages or on `localhost`, never on a plain `file://` page.

## Before you start
- No installs. Python is used only to serve the folder (`python -m http.server` is built into Python).
- No API key needed.

## Run it
1. From the course folder, go to this project and start a tiny web server:
   ```bash
   cd part-1-sound-basics/03-voice-recorder-in-the-browser
   python -m http.server 8000
   ```
2. Open http://localhost:8000/recorder.html in your browser.
3. Click **Start recording**. The browser asks for the microphone: click **Allow**.
4. Talk and watch the green bar move. Click **Stop**.
5. Play your recording, or click **download** to save it. Stop the server with `Ctrl+C` in the terminal.

### What you should see
In the terminal:
```
Serving HTTP on :: port 8000 (http://[::]:8000/) ...
::1 - - [15/Oct/2026 09:31:02] "GET /recorder.html HTTP/1.1" 200 -
```
On the page: a red **Start recording** button that turns green and says **Stop** while recording, a green meter that jumps when you talk (we measured about 20–60% of the width for normal speech), and after each stop a new line like:
```
9:31:15 AM · download
[ ▶ 0:00 / 0:04 ━━━━━━━━━━ 🔊 ]
```
Newest recordings appear at the top. Nothing is uploaded: the recordings only exist in this browser tab and disappear when you close it (unless you download them).

## How it works
Open `recorder.html`. The top half is styling (`<style>`) and the page layout (a button, a meter, a list). The interesting part is the `<script>`.

1. **The button does two jobs.** `btn.onclick` first checks `recorder.state === "recording"`. If it's recording, it calls `recorder.stop()` and returns. Otherwise it starts a new recording.
2. **Ask for the microphone.** `await navigator.mediaDevices.getUserMedia({ audio: true })` shows the permission pop-up and returns a `stream`. `await` means "wait for the answer before the next line". It's inside `try { } catch` so a blocked microphone shows a clear message instead of failing silently.
3. **Record.** `new MediaRecorder(stream)` creates the recorder. While recording, the browser hands over pieces of audio through `ondataavailable`, and we push them into `chunks`.
4. **When you stop**, `onstop` glues the pieces into one file: `new Blob(chunks, ...)`. A **Blob** is a file that lives in memory. `URL.createObjectURL(blob)` gives it a temporary address, which we use for both the `<audio>` player and the **download** link. Then it releases the microphone (`t.stop()`, so the browser's red recording dot goes away) and stops the meter.
5. **The live meter.** `new AudioContext()` starts the Web Audio system. `createMediaStreamSource(stream).connect(analyser)` sends the microphone into an `AnalyserNode`. Then `tick()` runs about 60 times a second (`requestAnimationFrame`): it reads the latest samples with `getFloatTimeDomainData`, computes RMS loudness exactly like project 02, and sets the green bar's width to `loudness * 400` percent (max 100%).

```
microphone ──getUserMedia──▶ stream ──┬──▶ MediaRecorder ──▶ chunks ──▶ Blob ──▶ <audio> + download
                                      └──▶ AnalyserNode ──▶ RMS 60×/s ──▶ green meter width
```

## If something goes wrong
- **Clicking the button does nothing, or you see "I can't use the microphone"** → you blocked the permission. Click the 🔒 (or camera/microphone) icon in the address bar, set Microphone to **Allow**, and reload.
- **`navigator.mediaDevices is undefined`** → you opened the file directly (`file:///...`) or from another computer's IP address over plain `http`. Open it as `http://localhost:8000/recorder.html`.
- **`OSError: [Errno 98] Address already in use`** → another program uses port 8000. Use another: `python -m http.server 8001`, then open `http://localhost:8001/recorder.html`.
- **The meter moves but the recording is silent** → the browser picked the wrong microphone. In Chrome, click the 🔒 icon → Site settings, or check your system's default input device.
- **Mac: no permission pop-up at all** → System Settings → Privacy & Security → Microphone → turn on your browser.

## Try this
1. **Easy:** make the meter turn red when you're too loud (loudness above 0.25).
   <details><summary>Hint</summary>Inside <code>tick()</code>, after setting the width, add:<br><code>document.getElementById("level").style.background = loudness > 0.25 ? "#e5484d" : "#3dd68c";</code></details>
2. **Medium:** show how many seconds you've been recording, on the button: "Stop (4 s)".
   <details><summary>Solution</summary>

   After `recorder.start();` add `const started = Date.now();`, then inside `tick()` add:
   ```js
   btn.textContent = `Stop (${Math.floor((Date.now() - started) / 1000)} s)`;
   ```
   The `onstop` handler already resets the text to "Start recording".
   </details>
3. **Harder:** stop recording automatically after 10 seconds.
   <details><summary>Hint</summary>After <code>recorder.start();</code> add <code>setTimeout(() => recorder.state === "recording" &amp;&amp; recorder.stop(), 10000);</code>. <code>setTimeout</code> runs a function once after a delay in milliseconds. The check avoids stopping twice if you already clicked Stop.</details>

## Check yourself
1. Why can't you just double-click `recorder.html` and use the microphone?
2. What is the difference between the `stream` and the `MediaRecorder`?
3. Why does the code call `t.stop()` on the stream's tracks when you stop?
4. The meter and project 02's loudness bar use the same maths. What is it?

<details><summary>Answers</summary>

1. Browsers only allow the microphone in a secure context: `https://` or `localhost`. A double-clicked file opens as `file://`, which isn't allowed.
2. The stream is the live sound coming from the microphone. The MediaRecorder listens to that stream and saves it into a compressed file.
3. To release the microphone. Otherwise the browser keeps it open and shows the recording indicator.
4. RMS: square each sample, average, take the square root.
</details>

## Learn more (optional)
- MDN, MediaStream Recording API: https://developer.mozilla.org/en-US/docs/Web/API/MediaStream_Recording_API
- MDN, Web Audio API basics: https://developer.mozilla.org/en-US/docs/Web/API/Web_Audio_API/Using_Web_Audio_API

## Next
→ [Part 2 · 04 · Transcribe a file with Whisper](../../part-2-speech-to-text/04-transcribe-a-file-with-whisper)
