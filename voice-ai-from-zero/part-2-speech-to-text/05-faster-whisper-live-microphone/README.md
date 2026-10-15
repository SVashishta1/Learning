# 05 · Faster Whisper + live microphone

**What you'll build:** a program that listens to your microphone non-stop and prints each phrase a moment after you pause. It uses **faster-whisper**, the same Whisper model rebuilt to run about 4× faster on a normal CPU.
**Like you're 10:** it's like a friend taking notes: they wait until you pause for breath, then write down what you just said.
**Time:** ~1.5 h · **Builds on:** [04 · Transcribe a file with Whisper](../04-transcribe-a-file-with-whisper) · **Needs:** a microphone (headphones help)

## Why this matters
Live captions (Google Meet, YouTube Live, phone accessibility features) and every voice assistant need speech-to-text *while* you talk, not after. Whisper isn't built for live streams, so real products use the trick you'll build here: collect sound, detect a pause, transcribe that piece. faster-whisper is what most open-source voice projects use in practice.

## What you'll learn
- **faster-whisper**: Whisper running on **CTranslate2**, a fast inference engine. Same accuracy, less time and memory.
- **int8 quantization**: storing the model's numbers as small whole numbers instead of decimals: smaller and faster on a CPU, with almost no loss in accuracy.
- **Callback + queue**: the microphone hands you sound in small pieces through a function it calls (a **callback**); a **queue** is the waiting line that passes those pieces to your main loop.
- **Pause detection (endpointing)**: deciding a phrase has ended because it has been quiet for a moment.

## Before you start
Same install as the rest of Part 2 (skip if done in project 04):
```bash
pip install openai-whisper faster-whisper "av<19" sounddevice soundfile numpy
```
- `faster-whisper`: the fast Whisper. `"av<19"`: keeps the audio-decoding library at a version that works with it.
- `sounddevice`: live microphone input. `numpy`: the loudness maths.

No API key needed. The first run downloads the `base` model (~145 MB) from Hugging Face into `~/.cache/huggingface/hub` (Windows: `C:\Users\<you>\.cache\huggingface\hub`).

## Run it
1. From the course folder:
   ```bash
   cd part-2-speech-to-text/05-faster-whisper-live-microphone
   python live.py
   ```
2. Wait for "Speak!", say a sentence, then pause for about a second. The text appears.
3. Keep going. Stop with `Ctrl+C`.

### What you should see
```
🎙️  Speak! (Ctrl+C to stop). I write each phrase after you pause.

📝 The quick brown fox jumps over the lazy dog. Machine learning is fun.
📝 Hello, I am speaking from your own computer. No internet needed.
^C
👋 Stopped.
```
Each 📝 line appears around 0.5–2 seconds after you stop talking. That delay is the 0.7 s pause the program waits for, plus Whisper's thinking time. Notice that short pauses *inside* a sentence don't split it: only a 0.7 s pause does.

## How it works
Open `live.py`.

1. **Load the model once.** `WhisperModel("base", device="cpu", compute_type="int8")`: `device="cpu"` runs on the processor, `compute_type="int8"` uses the small-number trick.
2. **The callback.** `sd.InputStream(..., blocksize=RATE // 10, callback=on_audio)` opens the microphone and calls `on_audio` with 1,600 new samples (0.1 s) ten times a second. `on_audio` does one quick thing: puts a copy of the sound into `heard`, a `queue.Queue`. It must be quick, because the microphone doesn't wait.
3. **The main loop** takes chunks out of the queue with `heard.get()` (which waits if the queue is empty) and adds them to `buffer`.
4. **Is anyone talking?** `np.sqrt(np.mean(chunk ** 2)) > 0.01` is the RMS loudness from project 02. Louder than 0.01 counts as "speech".
   - When it's loud: `spoke = True` and `silent_chunks` resets to 0.
   - When it's quiet: `silent_chunks` goes up by 1 (each one is 0.1 s).
5. **Before you start talking** (`not spoke`), the buffer keeps only the last 0.3 s (`buffer[-3:]`). That way silence doesn't pile up, but the very start of your first word isn't cut off.
6. **When to transcribe:** after 7 quiet chunks (0.7 s pause) or 150 chunks (15 s of non-stop talking). `np.concatenate(buffer)` joins the chunks into one array, the buffer is emptied, and `model.transcribe(...)` runs with:
   - `language="en"`: skip language detection (faster, and no wrong guesses on short phrases);
   - `vad_filter=True`: a small voice detector inside faster-whisper removes silent parts first, which stops Whisper inventing text in silence;
   - `beam_size=1`: take the single best guess at each step (faster; 5 is the default and slightly more accurate).
7. **`segments` is a generator**: the transcription actually happens while `" ".join(...)` reads it.
8. **`except KeyboardInterrupt`** catches `Ctrl+C` so the program ends with a friendly message instead of an error.

```
microphone ──0.1 s chunks──▶ on_audio() ──▶ queue ──▶ main loop: loud? ──▶ buffer
                                                            │
                                         0.7 s of quiet ────┘──▶ faster-whisper ──▶ 📝 text
```

## If something goes wrong
- **Nothing is ever printed** → your microphone is quieter than the `0.01` threshold, or blocked. Add `print(round(float(np.sqrt(np.mean(chunk ** 2))), 4))` inside the loop to see your loudness; set the threshold between your silence and your speech values. Check microphone permission (project 01).
- **Phrases print while nobody speaks** (fan, music) → raise `0.01` to `0.02` or `0.03`. Project 17 fixes this properly with a voice detector.
- **It cuts you off mid-sentence** → raise `silent_chunks >= 7` to `>= 10` (a 1 s pause).
- **An error that mentions `av` when transcribing a file** → you have version 19 of the `av` package, which faster-whisper 1.2 doesn't support yet. Run `pip install "av<19"`.
- **Text lags further and further behind** → your computer is too slow for `base`. Use `"tiny"` (or `"tiny.en"` for English).

## Try this
1. **Easy:** change `language="en"` to `language=None` and speak another language. It detects it automatically.
   <details><summary>Hint</summary>With <code>None</code>, Whisper detects the language for every phrase. Very short phrases can be misdetected; that's why we fix it to <code>"en"</code> by default. You can also get the detected language: <code>segments, info = model.transcribe(...)</code> then <code>info.language</code>.</details>
2. **Medium:** make it patient: wait for a 1-second pause, and show a dot every time a quiet chunk passes while you're talking.
   <details><summary>Hint</summary>Change <code>silent_chunks >= 7</code> to <code>>= 10</code>. In the <code>else:</code> branch add <code>if spoke: print(".", end="", flush=True)</code>.</details>
3. **Harder:** turn it into a voice diary: also save every phrase with the time to `diary.txt`.
   <details><summary>Solution</summary>

   Add `from datetime import datetime` at the top, then under `print("📝", text)`:
   ```python
   with open("diary.txt", "a", encoding="utf-8") as f:
       f.write(f"{datetime.now():%Y-%m-%d %H:%M}  {text}\n")
   ```
   `"a"` means *append*: add to the end instead of overwriting.
   </details>

## Check yourself
1. Why does `on_audio` only put the chunk in a queue, instead of transcribing it right there?
2. What two conditions trigger a transcription?
3. Why does the program keep the last 0.3 s of silence before you start talking?
4. What is the trade-off of `compute_type="int8"`?

<details><summary>Answers</summary>

1. The microphone calls it 10 times a second and won't wait. Transcribing takes much longer than 0.1 s, so sound would be lost. The queue lets the slow work happen in the main loop.
2. A 0.7 s pause after you spoke (`silent_chunks >= 7`), or 15 s of non-stop audio (`len(buffer) >= 150`).
3. The loudness check notices speech a little late, so the first sound of your first word would otherwise be cut off.
4. Much faster and smaller on a CPU, with a tiny loss of accuracy.
</details>

## Learn more (optional)
- faster-whisper on GitHub (speed comparisons, options): https://github.com/SYSTRAN/faster-whisper
- sounddevice's callback streams: https://python-sounddevice.readthedocs.io/en/latest/usage.html#callback-streams

## Next
→ [06 · Subtitles for any video](../06-subtitles-for-any-video)
