# 12 · Speech in the browser

**What you'll build:** one web page with two kinds of voices:
- **A.** the browser's **built-in voices** (`speechSynthesis`): instant, zero download;
- **B.** **Kokoro running inside the page** (`kokoro-js`): a real neural voice, downloaded once and then run fully on your device.

**Like you're 10:** the browser already knows how to read aloud in a robot voice. We also teach it to read in a human-sounding voice, without any server.
**Time:** ~1 h · **Builds on:** [11 · Studio-quality voices with Kokoro](../11-studio-quality-voices-with-kokoro) and [07 · Whisper inside the browser](../../part-2-speech-to-text/07-whisper-inside-the-browser) · **Needs:** Chrome or Edge, internet for the first Kokoro download (~90 MB)

## Why this matters
With project 07 (Whisper in the browser) and this project, a web page can both **listen** and **speak** with no server. That means complete voice apps that are private, free to host on any static website, and work offline after the first visit. Reading-aloud features on news sites, language-learning apps and accessibility tools use exactly these two options.

## What you'll learn
- **Web Speech API (`speechSynthesis`)**: the browser's built-in TTS, which uses your operating system's voices (like project 09).
- **`SpeechSynthesisUtterance`**: one "thing to say", with its text, voice and rate.
- **Dynamic `import()`**: loading a big library only when it's first needed, so the page opens instantly.
- **Blob + `<audio>`**: playing audio that was created in the page.

## Before you start
- No `pip install`, no API key. Python is only used to serve the folder.
- Part B downloads `kokoro-js` from the jsDelivr CDN and the Kokoro model (~90 MB) from Hugging Face the first time.

## Run it
1. From the course folder:
   ```bash
   cd part-3-text-to-speech/12-speech-in-the-browser
   python -m http.server 8000
   ```
2. Open http://localhost:8000 in Chrome or Edge.
3. Type something in the box.
4. **A:** pick a voice and click **Speak with the built-in voice**. It talks immediately.
5. **B:** pick a Kokoro voice and click **Speak with Kokoro**. The first time, wait for the download; then the audio player appears and plays.

### What you should see
- The **built-in voices** menu lists your system's voices, such as `Microsoft Aria Online (Natural) - English (United States) (en-US)` or `Google UK English Female (en-GB)` in Chrome. If your system has none, it shows `(your system's default voice)`.
- Under the Kokoro button, the status line changes:
  ```
  Loading Kokoro (first time only, ~90 MB)...
  Generating speech...
  Made in 2.3 s on your device.
  ```
  then an audio player appears and plays the sentence in a natural voice. The second click skips the loading step.

Compare the two: A is instant but flat; B takes a moment but sounds human.

## How it works
Open `index.html`. Two `<select>` menus, two buttons, a status line and a hidden `<audio>` player. The `<script type="module">` has two halves.

**A. Built-in voices**
1. `loadVoices()` reads `speechSynthesis.getVoices()` and fills the menu. Browsers load the voice list a little late, so it runs once at start and again on the `voiceschanged` event.
2. On click: `speechSynthesis.cancel()` stops any previous speech. `new SpeechSynthesisUtterance(text)` creates the thing to say; we set `.voice` (the selected one, or `null` for the default) and `.rate` (1.0 = normal). `speechSynthesis.speak(say)` says it.

**B. Kokoro in the page**
3. The first click runs `await import("https://cdn.jsdelivr.net/npm/kokoro-js@1.2.1/+esm")`. A **dynamic import** downloads the library only now, not when the page opens. `@1.2.1` pins the version.
4. `KokoroTTS.from_pretrained("onnx-community/Kokoro-82M-v1.0-ONNX", { dtype: "q8", device: "wasm" })` downloads the model (8-bit numbers = ~90 MB) and prepares it to run on the CPU with WebAssembly. It's kept in the `tts` variable, so later clicks reuse it.
5. `await tts.generate(text, { voice })` runs the same Kokoro model as project 11, but in JavaScript. It returns audio; `.toBlob()` makes it a WAV file in memory, `URL.createObjectURL(...)` gives it an address, and the `<audio>` player plays it.
6. `performance.now()` before and after measures the time. `try { } catch` shows any error in the status line, and the button is disabled while working so you can't click twice.

```
A: text ──▶ speechSynthesis ──▶ your OS's voice ──▶ 🔊                     (instant, robotic)
B: text ──▶ kokoro-js (Kokoro model, in the tab) ──▶ WAV Blob ──▶ <audio> ──▶ 🔊   (natural, private)
```

## If something goes wrong
- **"Error: Failed to fetch"** → the library or model couldn't download. Check your internet; some networks block `cdn.jsdelivr.net` or `huggingface.co`.
- **The built-in menu shows only "(your system's default voice)"** → your OS has no extra voices installed (common on Linux). Install some (Windows: Settings → Time & language → Speech; Linux: `sudo apt install espeak-ng`), or use Chrome, which adds online "Google" voices.
- **Built-in voice says nothing** → check the volume. Firefox on Linux needs `speech-dispatcher` installed.
- **Kokoro is very slow or the tab crashes** → it runs on the CPU and needs ~500 MB of memory. Close other tabs and use short sentences. Try exercise 1 (WebGPU) on a recent computer.
- **No sound from Kokoro, but the player appears** → press ▶ on the player. Some browsers block automatic playback until you've interacted with the page.

## Try this
1. **Easy:** run Kokoro on the graphics card. Is it faster on your machine?
   <details><summary>Hint</summary>Change <code>device: "wasm"</code> to <code>"webgpu"</code> and <code>dtype: "q8"</code> to <code>"fp32"</code> (WebGPU works best with full-precision numbers; the download becomes ~330 MB). Compare the "Made in" times. If you get an error, your browser or GPU doesn't support WebGPU: switch back.</details>
2. **Medium:** add a speed slider that works for both voices.
   <details><summary>Solution</summary>

   Add to the page: `<label>Speed <input id="speed" type="range" min="0.5" max="2" step="0.1" value="1"></label>`. Then:
   - in part A, replace `say.rate = 1.0;` with `say.rate = Number($("speed").value);`
   - in part B, use `tts.generate($("text").value, { voice: $("kvoice").value, speed: Number($("speed").value) })`.
   </details>
3. **Harder:** add all of Kokoro's English voices to the menu automatically, instead of the five written by hand.
   <details><summary>Hint</summary>After loading <code>tts</code>, <code>tts.list_voices()</code> prints a table of voices to the console, and <code>Object.keys(tts.voices)</code> gives their names. Fill <code>$("kvoice").innerHTML</code> with an <code>&lt;option&gt;</code> for each name, like <code>loadVoices()</code> does.</details>

## Check yourself
1. Where do the built-in voices come from, and why do they differ between computers?
2. Why does the page use `await import(...)` inside the click handler instead of importing kokoro-js at the top?
3. After the first Kokoro run, does the text you type get sent anywhere?
4. When would you choose the built-in voice over Kokoro?

<details><summary>Answers</summary>

1. From the operating system (and, in Chrome/Edge, some online voices). Each OS and installation has a different set.
2. So the page opens instantly and people who only use the built-in voices never download ~90 MB.
3. No. The model is already in the browser; text and audio stay on your device.
4. When speed and zero download matter more than quality: quick alerts, slow devices, or users with limited data.
</details>

## Learn more (optional)
- MDN, Web Speech API (speech synthesis): https://developer.mozilla.org/en-US/docs/Web/API/SpeechSynthesis
- kokoro-js on npm: https://www.npmjs.com/package/kokoro-js

## Next
→ [Part 4 · 13 · Voice notes app](../../part-4-voice-apps/13-voice-notes-app)
