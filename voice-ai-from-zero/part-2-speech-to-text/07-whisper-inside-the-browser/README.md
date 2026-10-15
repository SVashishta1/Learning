# 07 · Whisper inside the browser

**What you'll build:** a web page that runs Whisper **inside your browser**. Record or pick a file and get a transcript with **no server, no Python and no upload**: the model downloads once and then runs on your own device (on the graphics card when the browser supports WebGPU).
**Like you're 10:** instead of sending your voice to a computer far away, the web page brings the whole "ears" model to *your* computer and does the work there.
**Time:** ~1 h · **Builds on:** [06 · Subtitles for any video](../06-subtitles-for-any-video) and the browser recorder from [03](../../part-1-sound-basics/03-voice-recorder-in-the-browser) · **Needs:** Chrome or Edge (Firefox and Safari also work, more slowly), internet for the first model download

## Why this matters
"On-device AI" is a big trend: it's private (audio never leaves the device), free to run (no server bills), and works offline after the first load. Apps like note-takers, language-learning sites and accessibility tools now ship models this way. The library you use here, **transformers.js**, runs thousands of Hugging Face models in JavaScript.

## What you'll learn
- **transformers.js**: a JavaScript library that runs the same AI models as Python, in a web page.
- **WebGPU vs WebAssembly (WASM)**: two ways a browser can do heavy maths. WebGPU uses the graphics card (fast); WASM uses the processor (works everywhere).
- **Quantization (`dtype`)**: storing a model's numbers with fewer bits (`q8` = 8-bit, `q4` = 4-bit) so it downloads faster and runs faster, with a small accuracy cost.
- **Browser cache**: the model is saved by the browser after the first download, so the next visit loads in seconds.

## Before you start
- No `pip install` and no API key. Python is only used to serve the folder (`python -m http.server` is built in).
- The page loads transformers.js from the jsDelivr CDN and the model from Hugging Face, so the **first** run needs internet.

## Run it
1. From the course folder:
   ```bash
   cd part-2-speech-to-text/07-whisper-inside-the-browser
   python -m http.server 8000
   ```
2. Open http://localhost:8000 in **Chrome or Edge**.
3. Pick a model (start with **base**), then click **🎙️ Record**, allow the microphone, talk, and click **⏹ Stop and transcribe**. Or click **📁 Pick an audio file** and choose any recording (for example project 01's `my_voice.wav`).
4. The first time, wait for the download. Then the transcript appears.

### What you should see
The status line under the buttons goes through these steps:
```
Recording...
Downloading onnx-community/whisper-base (only the first time)...
Downloading onnx/encoder_model.onnx: 63%
Transcribing 5.0 s of audio...
Done in 1.4 s on your GPU (WebGPU).
```
and the big box shows your words, for example:
```
The quick brown fox jumps over the lazy dog. Machine learning is fun.
```
On a computer without WebGPU it says `on your CPU (WebAssembly)` and takes a few seconds longer. Record a second time: no download now, it's cached.

To check it really runs on your device: after the first download, turn off Wi-Fi and transcribe again. It still works.

## How it works
Open `index.html`. The page has a model menu, two buttons, a status line and an output box. Everything else is in the `<script type="module">` (a "module" can `import` code from a URL).

1. **Import the library.** `import { pipeline } from "https://cdn.jsdelivr.net/npm/@huggingface/transformers@4.2.0"` downloads transformers.js. The `@4.2.0` pins the version, so the page doesn't break when a new version comes out.
2. **Pick the engine.** `navigator.gpu?.requestAdapter()` asks "is there a usable graphics card?". If yes, `device = "webgpu"`, otherwise `"wasm"`.
3. **`getTranscriber()`** creates the model once and reuses it (unless you choose another model in the menu). `pipeline("automatic-speech-recognition", name, { device, dtype, progress_callback })` downloads the model files and prepares them. `dtype` says how precise the numbers should be:
   - on WebGPU: `fp32` (full precision) for the **encoder**, which reads the audio, and `q4` for the **decoder**, which writes the words;
   - on WASM: `q8` for everything, the safest choice for processors.
   `progress_callback` is called while files download, so we can show percentages.
4. **`transcribe(blob)`** gets audio ready for Whisper. `new AudioContext({ sampleRate: 16000 })` plus `decodeAudioData(...)` turns any recording (webm, mp3, wav...) into 16,000 numbers per second, exactly like ffmpeg did in Python. `getChannelData(0)` takes the first channel (mono).
5. **Run Whisper.** `await t(audio, { chunk_length_s: 30, stride_length_s: 5 })` transcribes. Whisper reads 30 seconds at a time, so long audio is cut into 30 s pieces that overlap by 5 s (so no word is cut in half), and the texts are joined.
6. **Record button.** The same `MediaRecorder` code as project 03. When you stop, the recording is passed to `transcribe(...)`. The file picker (`$("file").onchange`) passes the chosen file instead.
7. **Errors** are caught with `try { } catch` and shown in the status line instead of failing silently.

```
microphone or file ──▶ AudioContext (16 kHz mono) ──▶ transformers.js + Whisper (WebGPU or WASM) ──▶ text
                                 everything inside your browser tab; only the model is downloaded, once
```

## If something goes wrong
- **"Something went wrong: Failed to fetch"** → the model couldn't download. Check your internet, then try again. Some school/work networks block `huggingface.co` or `cdn.jsdelivr.net`.
- **The page stays on "Ready." and the buttons do nothing** → the library didn't load. Open the browser console (F12 → Console) to see the error. Make sure you opened `http://localhost:8000`, not the file directly.
- **"I can't use the microphone"** → allow it via the 🔒 icon in the address bar. Microphones only work on `localhost` or `https://`.
- **It's very slow or the tab crashes with `small`** → your device doesn't have enough memory or no WebGPU. Use `tiny.en` or `base`.
- **WebGPU errors in the console** → some graphics drivers have WebGPU bugs. Force the CPU path: change the `device` line to `const device = "wasm";`.

## Try this
1. **Easy:** transcribe the same recording with `tiny.en` and with `base`. Compare speed and accuracy.
   <details><summary>Hint</summary>Use 📁 Pick an audio file with the same file each time, so the test is fair. The status line shows the time. <code>tiny.en</code> is English-only but fast; <code>base</code> knows 99 languages.</details>
2. **Medium:** show time stamps, like project 04 did in Python.
   <details><summary>Solution</summary>

   Change the transcribe call and the output line:
   ```js
   const result = await t(audio, { chunk_length_s: 30, stride_length_s: 5, return_timestamps: true });
   $("out").textContent = result.chunks
     .map(c => `[${c.timestamp[0].toFixed(1)}s → ${(c.timestamp[1] ?? 0).toFixed(1)}s] ${c.text.trim()}`)
     .join("\n");
   ```
   With `return_timestamps: true` the result has a `chunks` list; each chunk has `timestamp: [start, end]` and `text`.
   </details>
3. **Harder:** add a **Download .txt** button that saves the transcript.
   <details><summary>Hint</summary>Add <code>&lt;button id="save"&gt;💾 Download .txt&lt;/button&gt;</code> to the page, then:<br><code>$("save").onclick = () => { const a = document.createElement("a"); a.href = URL.createObjectURL(new Blob([$("out").textContent])); a.download = "transcript.txt"; a.click(); };</code><br>It's the same Blob + object URL trick as the download link in project 03.</details>

## Check yourself
1. Why is this page more private than an app that sends your audio to a server?
2. What is the difference between `device: "webgpu"` and `device: "wasm"`?
3. Why does the code convert the audio to 16,000 samples per second before transcribing?
4. Why is the second transcription much faster to start than the first?

<details><summary>Answers</summary>

1. Only the model is downloaded; your audio is processed inside your browser and never sent anywhere.
2. WebGPU runs the maths on the graphics card (fast, but not available everywhere); WASM runs it on the processor (slower, works in every modern browser).
3. Whisper was trained on 16 kHz mono audio and expects exactly that format.
4. The model is already loaded in memory (and saved in the browser's cache), so there is nothing to download.
</details>

## Learn more (optional)
- transformers.js docs: https://huggingface.co/docs/transformers.js
- Official examples (Whisper WebGPU and more): https://github.com/huggingface/transformers.js-examples
- Search YouTube for "transformers.js whisper webgpu".

## Next
→ [08 · Any language → English](../08-any-language-to-english)
