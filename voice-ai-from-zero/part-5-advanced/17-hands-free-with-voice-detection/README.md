# 17 · Hands-free with voice detection

**What you'll build:** two small programs that use **Silero VAD** (Voice Activity Detection), a tiny neural network that knows *exactly* when someone is speaking:
- `find_speech.py` lists the speech parts of any recording;
- `hands_free.py` listens to your microphone and writes down each sentence as soon as you finish it, with no button and no Enter key.

**Like you're 10:** our old trick (project 05) only asked "is it loud?", so a door slam counted as talking. Silero asks "does this sound like a human voice?".
**Time:** ~1.5 h · **Builds on:** [16 · Voice assistant web app](../../part-4-voice-apps/16-voice-assistant-web-app) and the pause trick from [05](../../part-2-speech-to-text/05-faster-whisper-live-microphone) · **Needs:** a microphone (headphones help)

## Why this matters
Every hands-free product needs **turn detection**: knowing when you start and stop talking. Smart speakers, phone bots and video-call noise suppression all use a VAD. Silero VAD is the open-source standard: 2 MB, runs in under a millisecond per chunk on a CPU, and is even used *inside* faster-whisper (`vad_filter=True` in earlier projects). It's also how long recordings are trimmed before transcription, which saves time and stops Whisper inventing text in silence.

## What you'll learn
- **VAD (voice activity detection)**: a model that outputs "probability that this tiny slice of audio is human speech".
- **Threshold**: how sure the VAD must be (0.5 = 50%) before it calls something speech.
- **Speech start/end events**: `VADIterator` turns probabilities into "speech started" / "speech ended" moments.
- **Pre-roll buffer**: keeping the last fraction of a second *before* speech was detected, so the first syllable isn't cut off.
- **Tensor**: PyTorch's version of a numpy array; models built with PyTorch expect tensors.

## Before you start
Part 5 builds on Part 4's packages. Install the extra ones (skip what you have):
```bash
pip install faster-whisper "av<19" sounddevice numpy silero-vad jiwer scipy
```
- `silero-vad`: the voice detector. It needs **PyTorch** (`torch`), which pip installs if you don't already have it from project 04 (it's big: about 200 MB on Windows/Mac and up to ~3 GB on Linux).
- `faster-whisper`: transcribes each sentence; `decode_audio` from it reads any audio file.
- `sounddevice` + `numpy`: the microphone stream.
- `jiwer` and `scipy` are for project 21.

No API key needed. The VAD model is inside the pip package, so nothing to download; Whisper `base` is reused from earlier projects.

## Run it
1. From the course folder:
   ```bash
   cd part-5-advanced/17-hands-free-with-voice-detection
   ```
2. Find the speech in a file (with no file name it uses project 01's `my_voice.wav`):
   ```bash
   python find_speech.py ../../part-1-sound-basics/01-record-and-play-your-voice/my_voice.wav
   ```
3. Hands-free listening: run it, then just talk in sentences with natural pauses. Clap or play instrumental music in between. Stop with `Ctrl+C`.
   ```bash
   python hands_free.py
   ```

### What you should see
`find_speech.py` on a 12-second recording with two sentences:
```
🗣️    1.00s →   3.60s
🗣️    4.00s →   5.60s
🗣️    7.70s →  11.40s

7.9 s of speech in 12.4 s of audio (64%)
```
`hands_free.py` (we fed it the same recording):
```
🎧 Just talk. (Ctrl+C to stop)
📝 The quick brown fox jumps over the lazy dog. Machine learning is fun.
📝 Hello, I am speaking from your own computer. No internet needed.
^C
👋 Stopped.
```
While you talk, the line shows `🟢 speaking...`; the 📝 text replaces it when you stop. We also played claps, chords and hiss to `find_speech.py`: it found `0.0 s of speech`. Music *with singing* does count as voice, of course.

With recent PyTorch versions you may also see `FutureWarning: torch.jit.load is deprecated`. That's a warning from inside the silero-vad package, not an error: ignore it.

## How it works
**`find_speech.py`** (offline, on a whole file)
1. `load_silero_vad()` loads the 2 MB model that ships inside the package.
2. `decode_audio(path)` (from faster-whisper) reads any audio/video file as 16 kHz mono numbers; `torch.from_numpy(...)` turns them into a PyTorch **tensor**.
3. `get_speech_timestamps(audio, vad, ...)` runs the VAD over the whole file in 32 ms slices and joins the "speech" slices into parts. `min_silence_duration_ms=300` means pauses shorter than 0.3 s don't split a part. `return_seconds=True` gives times in seconds.
4. The loop prints each part; the last line adds them up and compares with the total length.

**`hands_free.py`** (live, from the microphone)
5. **Settings.** `CHUNK = 512`: Silero listens to exactly 512 samples (32 ms at 16 kHz) at a time, so the microphone stream uses `blocksize=CHUNK`. `VADIterator(..., threshold=0.5, min_silence_duration_ms=600)` means "≥50% sure it's a voice" and "0.6 s of non-voice = you finished".
6. **`before = deque(maxlen=10)`**: a **deque** with a maximum length drops the oldest item when a new one arrives, so it always holds the last 10 chunks (0.3 s). This is the pre-roll.
7. **The loop** takes each chunk from the queue and asks the VAD `vad(torch.from_numpy(chunk))`. It returns `None` most of the time, `{"start": ...}` when speech begins, and `{"end": ...}` when it ends.
   - On **start**: `talking = True` and `speech = list(before)` (begin with the 0.3 s before the voice was noticed).
   - While talking, chunks go into `speech`; otherwise into `before`.
   - On **end**: `np.concatenate(speech)` → Whisper → print the sentence.

```
mic ──32 ms chunks──▶ Silero VAD: voice? ──"start"──▶ collect chunks (plus 0.3 s pre-roll)
                                         ──"end"────▶ Whisper ──▶ 📝 sentence
```

Compared with project 05: the loudness check is replaced by a voice check, and the "0.7 s of quiet" rule by the VAD's "0.6 s of non-voice".

## If something goes wrong
- **It never triggers** → your microphone is very quiet or blocked. Lower `threshold` to `0.3`, and check permission (project 01).
- **Background noise or a TV triggers it** → raise `threshold` to `0.6`–`0.7`. A TV with people talking *is* voice: use headphones or move away.
- **It cuts you off while you think mid-sentence** → raise `min_silence_duration_ms` to `900` or `1000`.
- **`ValueError: Provided number of samples is 1024 (Supported values: 256 for 8000 sample rate, 512 for 16000)`** → the chunk size must be exactly 512 at 16 kHz. Keep `blocksize=CHUNK` and `RATE = 16000`.
- **`ModuleNotFoundError: No module named 'silero_vad'`** → activate your venv and run the pip line (the package name has a dash: `silero-vad`).

## Try this
1. **Easy:** make `find_speech.py` stricter about pauses: only split on gaps of 1 second or more. How many parts do you get now?
   <details><summary>Hint</summary>Change <code>min_silence_duration_ms=300</code> to <code>1000</code>. Short breaths between words no longer split the speech, so you get fewer, longer parts, which is what you'd want before transcribing a lecture.</details>
2. **Medium:** watch the VAD think: print its speech probability for every chunk while you talk, whisper and clap.
   <details><summary>Solution</summary>

   In `hands_free.py`, right after `chunk = mic.get()`, add:
   ```python
   p = vad.model(torch.from_numpy(chunk), RATE).item()
   print(f"{p:.2f} " + "█" * int(p * 30))
   ```
   `vad.model` is the raw network inside the `VADIterator`; `.item()` turns the 1-number tensor into a Python float. Talking gives values near 1.0, silence near 0.0, a clap stays low. (It prints 31 lines per second, so remove it when you're done.)
   </details>
3. **Harder:** make project 15's conversation hands-free: replace its `record()` with a VAD listener.
   <details><summary>Hint</summary>In <code>talk.py</code>, write a <code>record()</code> that opens an <code>sd.InputStream</code> with <code>blocksize=512</code> and a queue, runs the same loop as <code>hands_free.py</code>, and <code>return np.concatenate(speech)</code> on the first <code>"end"</code> event (create a new <code>VADIterator</code> each time, or call <code>vad.reset_states()</code>). Use headphones, or the assistant will hear its own answers.</details>

## Check yourself
1. Why does a clap trigger project 05's listener but not this one?
2. What is the `before` deque for, and what would happen without it?
3. Why does `hands_free.py` read the microphone in blocks of exactly 512 samples?
4. You want the assistant to answer faster after you stop talking. Which setting do you change, and what's the risk?

<details><summary>Answers</summary>

1. Project 05 only checks loudness, and a clap is loud. Silero checks whether the sound *looks like a human voice*, which a clap doesn't.
2. It keeps the last 0.3 s of audio. The VAD notices speech a few chunks after it starts; without the pre-roll, the start of the first word would be cut off.
3. Silero VAD at 16 kHz only accepts 512-sample windows (32 ms).
4. Lower `min_silence_duration_ms` (e.g. to 300). The risk: it decides you've finished during a short thinking pause and cuts you off.
</details>

## Learn more (optional)
- Silero VAD on GitHub (examples, accuracy charts): https://github.com/snakers4/silero-vad
- Search YouTube for "voice activity detection explained".

## Next
→ [18 · Who spoke when](../18-who-spoke-when)
