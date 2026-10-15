# 11 · Studio-quality voices with Kokoro

**What you'll build:** a program that speaks with **Kokoro-82M**, one of the most natural open-source voices available. It has 50+ voices (American, British and 7 other languages), runs on a normal CPU, and you'll **mix two voices** into a brand-new one.
**Like you're 10:** each Kokoro voice is stored as a list of numbers. Average two lists, and you get a voice that has never existed.
**Time:** ~1 h · **Builds on:** [10 · Natural voices with Piper](../10-natural-voices-with-piper) · **Needs:** ~340 MB of free disk for the model files (downloaded once)

## Why this matters
Kokoro sounds close to paid cloud voices, but it's free (Apache licence), small (82 million numbers, tiny for a modern model) and private. It's a popular choice for audiobook tools, podcasts made from text, and local assistants. You'll use it as the "mouth" in projects 15, 16, 19 and 21.

## What you'll learn
- **Parameters**: the learned numbers inside a model. "82M" = 82 million. Big LLMs have billions; Kokoro is small and fast.
- **Style vector (voice embedding)**: a voice stored as numbers, separate from the model, which is why one model can have 50+ voices.
- **Voice mixing**: averaging two style vectors creates an in-between voice.
- **Model caching**: download big files once, into one shared folder, and reuse them.

## Before you start
Same install as the rest of Part 3 (skip if done):
```bash
pip install pyttsx3 piper-tts kokoro-onnx soundfile sounddevice numpy
```
- `kokoro-onnx`: runs Kokoro with **ONNX Runtime**, a light engine that works on Python 3.10–3.13 without PyTorch.
- `numpy`: mixes the voices. `soundfile`/`sounddevice`: save and play.

No API key needed. The first run downloads two files from the kokoro-onnx project on GitHub into **`voice-ai-from-zero/models/`** (the course folder): `kokoro-v1.0.onnx` (~310 MB, the model) and `voices-v1.0.bin` (~27 MB, all the voices). Every later project that speaks with Kokoro finds them there, so you download them only once.

## Run it
1. From the course folder:
   ```bash
   cd part-3-text-to-speech/11-studio-quality-voices-with-kokoro
   ```
2. Run it with the default voice (the first run waits for the download):
   ```bash
   python kokoro_speak.py
   ```
3. Choose your own text and voice:
   ```bash
   python kokoro_speak.py "Welcome to my podcast about AI." am_michael
   ```

### What you should see
```
Downloading kokoro-v1.0.onnx into .../voice-ai-from-zero/models (once, please wait)...
Downloading voices-v1.0.bin into .../voice-ai-from-zero/models (once, please wait)...
Some voices: af_alloy, af_aoede, af_bella, af_heart, af_jessica, af_kore, af_nicole, af_nova, af_river, af_sarah, af_sky, am_adam ...
🔊 af_heart: 4.8 s of speech, made in 12.4 s → kokoro.wav
🔊 mixed voice (50% af_heart + 50% bf_emma) → kokoro_mixed.wav
```
- The two "Downloading" lines appear only the first time.
- We ran this on a slow 4-core cloud computer, so 4.8 s of speech took 12.4 s. A typical laptop is 2–5× faster; Kokoro is slower than Piper but sounds noticeably more human.
- Listen to `kokoro_mixed.wav`: it's neither af_heart (American) nor bf_emma (British), but something in between.

## How it works
Open `kokoro_speak.py`.

1. **Find the shared models folder.** `Path(__file__).resolve().parents[2] / "models"`: `__file__` is this script; `parents[0]` is its folder, `parents[1]` is `part-3-text-to-speech`, `parents[2]` is the course folder. So the files go to `voice-ai-from-zero/models/`.
2. **Download once.** For each file that's missing, `urllib.request.urlretrieve(...)` downloads it to `name.part`, and only after it finishes `.rename(...)` gives it the real name. If the download is interrupted, the next run starts again instead of using a broken file.
3. **Load.** `Kokoro(model, voices)` loads the model into ONNX Runtime and reads the voice file.
4. **Choose text and voice** from the command line (`sys.argv`), with defaults. Voice names: first letter = language/accent (`a` American, `b` British, `e` Spanish, `f` French, `h` Hindi, `i` Italian, `j` Japanese, `p` Portuguese, `z` Chinese), second letter = `f`emale or `m`ale.
5. **Speak.** `kokoro.create(text, voice=voice, speed=1.0, lang="en-us")` turns the text into phonemes (like Piper) and runs the model with that voice's style vector. It returns `samples` (the audio numbers) and `rate` (24,000 per second).
6. **Save and play.** `sf.write(...)`, then `sd.play(...)` + `sd.wait()`.
7. **Mix two voices.** `kokoro.get_voice_style("af_heart")` returns that voice's numbers (a numpy array of shape 510 × 1 × 256). Multiply each by 0.5 and add them with `np.add(...)`: a 50/50 average. Pass the array as `voice=mixed` instead of a name.

```
text ──▶ phonemes ──▶ Kokoro model ◀── style vector (af_heart, or a mix of two)
                           │
                           ▼
                  24,000 samples/s ──▶ kokoro.wav ──▶ 🔊
```

## If something goes wrong
- **`ModuleNotFoundError: No module named 'kokoro_onnx'`** → activate your venv and re-run the pip line. (The package is `kokoro-onnx`; the separate `kokoro` package needs PyTorch and doesn't install on Python 3.13.)
- **The download is very slow or fails** → run the script again: files that finished are kept, and only the unfinished one downloads again. Or download both files in your browser from https://github.com/thewh1teagle/kokoro-onnx/releases/tag/model-files-v1.0 and put them in `voice-ai-from-zero/models/`.
- **`ValueError: Voice am_mike not found in available voices`** → that voice name doesn't exist. The script prints some names; `print(kokoro.get_voices())` lists all 54.
- **`[ONNXRuntimeError] : 7 : INVALID_PROTOBUF ... Protobuf parsing failed`** → the model file is damaged (for example, you copied a half-downloaded file). Delete `models/kokoro-v1.0.onnx` and run again.
- **It's slow** → short sentences are faster. In projects 15, 16 and 19 we speak short answers, and project 19 speaks one sentence at a time while the next one is made.

## Try this
1. **Easy:** try `bf_emma`, `am_adam`, `af_bella` and `bm_george`. Which do you like best?
   <details><summary>Hint</summary><code>python kokoro_speak.py "Hello there, how are you today?" bf_emma</code>, then the others. Each run overwrites <code>kokoro.wav</code>.</details>
2. **Medium:** make a 70/30 mix instead of 50/50, and speak 20% faster.
   <details><summary>Hint</summary>Change the two <code>0.5</code>s to <code>0.7</code> and <code>0.3</code> (they should add up to 1.0). Add <code>speed=1.2</code> to the second <code>kokoro.create(...)</code> call.</details>
3. **Harder:** read a whole text file aloud and save it as one audio file, like a mini audiobook.
   <details><summary>Solution</summary>

   Create `story.txt` in this folder, then change the text line to:
   ```python
   text = Path("story.txt").read_text(encoding="utf-8")
   ```
   `kokoro.create` splits long text into pieces internally and joins the audio, so a few paragraphs work fine (it takes a while; watch the "made in" time). For a book, do it chapter by chapter.
   </details>

## Check yourself
1. Why can one Kokoro model speak in 50+ different voices?
2. What does `np.add(a * 0.5, b * 0.5)` produce, and why does it work as a voice?
3. Why does the script download to a `.part` file first?
4. Why are the model files kept in `voice-ai-from-zero/models/` instead of this project's folder?

<details><summary>Answers</summary>

1. The model learned to speak in *any* style; each voice is a small set of numbers (a style vector) that tells it which style to use.
2. The average of the two voices' style vectors. Because voices are numbers in the same "space", the average is a valid in-between voice.
3. So a half-downloaded file never gets the real name. Otherwise the next run would think it's complete and fail to load it.
4. Five projects use Kokoro. One shared copy saves about 1.3 GB of disk and four downloads.
</details>

## Learn more (optional)
- kokoro-onnx on GitHub: https://github.com/thewh1teagle/kokoro-onnx
- Kokoro-82M model card (voices, languages, licence): https://huggingface.co/hexgrad/Kokoro-82M
- Search YouTube for "Kokoro TTS local" for demos.

## Next
→ [12 · Speech in the browser](../12-speech-in-the-browser)
