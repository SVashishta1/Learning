# 21 · Measure accuracy

**What you'll build:** a benchmark that answers "which Whisper size is good enough for me?" with numbers instead of guesses. It makes test audio with Kokoro (so the correct words are known), adds a noisy copy, runs Whisper `tiny`, `base` and `small` on everything, and prints the **Word Error Rate** and **speed** of each, plus every sentence it got wrong.
**Like you're 10:** it's a spelling test for Whisper. We read it sentences we already know, then count how many words it wrote down wrong.
**Time:** ~1.5 h · **Builds on:** [20 · Clone your own voice](../20-clone-your-own-voice), Whisper from [Part 2](../../part-2-speech-to-text) and Kokoro from [11](../../part-3-text-to-speech/11-studio-quality-voices-with-kokoro) · **Needs:** ~1 GB of disk for three Whisper sizes, 5–15 minutes of CPU time

## Why this matters
"It seems to work" isn't good enough for a product. Every speech-recognition paper, model card and vendor comparison reports **WER**, and engineers choose models by measuring WER and speed *on their own kind of audio*. Being able to run a small, fair benchmark is one of the most useful skills in applied AI: it turns opinions into decisions.

## What you'll learn
- **WER (Word Error Rate)** = (wrong + missing + extra words) ÷ number of words in the correct text. 0% is perfect; under 5% is very good.
- **Ground truth**: the known correct answer you compare against.
- **Real-time factor (×RT)**: `10x RT` means 1 minute of audio is transcribed in 6 seconds. A live assistant needs well above `1x`.
- **Normalisation**: making texts comparable before scoring (lower case, no punctuation, single spaces). Without it, "Hello," vs "hello" would count as an error.
- **Synthetic test data**: generating test audio with TTS. Quick and repeatable, but real voices and microphones are harder.

## Before you start
Part 5's packages (skip what you have):
```bash
pip install faster-whisper "av<19" kokoro-onnx soundfile numpy silero-vad jiwer scipy
```
- `jiwer`: computes WER.
- `scipy`: `resample_poly` converts Kokoro's 24 kHz audio to Whisper's 16 kHz.
- `kokoro-onnx`: makes the test sentences; `faster-whisper`: the models being tested.

No API key needed. The first run downloads Whisper `tiny` (75 MB), `base` (145 MB) and `small` (~480 MB) if you don't have them, and reuses Kokoro from `voice-ai-from-zero/models/`. No microphone needed.

## Run it
1. From the course folder:
   ```bash
   cd part-5-advanced/21-measure-accuracy
   python benchmark.py
   ```
2. Wait. Making the audio takes a minute, then each model runs on 12 clips (6 clean + 6 noisy).

### What you should see
These are real rows from our test machine for `base` (your table also has `tiny` and `small` rows, and your numbers will differ):
```
Making the test audio with Kokoro...
model    audio     WER        speed
base     clean    9.4%       2.5x RT
         ✗ Please book a table for 4 people at 7.30 tomorrow evening.
         ✗ My flight to Barcelona leaves from Gate 12 at noon.
         ✗ Turn off the kitchen lights and set an alarm for 6 in the morning.
         ✗ She sells seashells by the seashore on sunny Saturday.
base     noisy   32.8%       3.0x RT
         ✗ Quick round bar, jumps over the lazy jump.
         ✗ Please book a table for four people at 7.30 tomorrow evening.
         ...
         ✗ [Music]  Need a bath? Good
         ✗ She sells feed shells by the feed shell on Sunday Saturday.
```
How to read it:
- Each ✗ line is what Whisper wrote for a sentence it didn't get exactly right.
- On clean audio, 3 of the 4 "mistakes" are numbers: Whisper wrote `4`, `7.30`, `12`, `6` for "four", "seven thirty", "twelve", "six". They aren't really wrong, but this simple benchmark counts them. Serious benchmarks convert numbers before comparing (try exercise 2).
- Noise makes everything much worse (9% → 33%), and Whisper even "heard" `[Music]` in the hiss. Your microphone and room matter as much as the model.
- Typically `tiny` is fastest with the most errors, and `small` is slowest with the fewest. Pick the smallest model whose WER is acceptable *for your audio*.

## How it works
Open `benchmark.py`.

1. **The test set.** `SENTENCES` holds six sentences with tricky parts: numbers, a place name, a tongue-twister. These are the **ground truth**.
2. **`clean(text)`** normalises a text: lower-case, keep only letters, digits, apostrophes and spaces (`re.sub(r"[^a-z0-9' ]", "", ...)`), then `" ".join(....split())` squashes repeated spaces.
3. **Make the audio.** Each sentence is spoken by a different Kokoro voice (`zip(SENTENCES, voices)` pairs them up), so it's not just one easy voice. `resample_poly(samples, 2, 3)` changes 24,000 samples/s into 16,000 (× 2 ÷ 3).
4. **Make it noisy.** `noise.standard_normal(len(c))` creates random hiss (`default_rng(0)` makes it the same every run, so results are comparable), scaled by `0.05` and added to each clip.
5. **Test every model.** For each size, load `WhisperModel(size, ...)`, transcribe every clip of each condition with `language="en", beam_size=1`, and time it. `jiwer.wer(truths, guesses)` lines up the words of each pair and counts substitutions, deletions and insertions, divided by the total number of correct words.
6. **Speed.** `audio_seconds / seconds` = how many seconds of audio per second of computing: the real-time factor.
7. **Show the mistakes.** Any sentence whose cleaned text differs from the truth is printed with ✗, so you can see *what kind* of errors happen.

```
SENTENCES ──Kokoro──▶ clean clips ──+ hiss──▶ noisy clips
                          │                       │
                          └──▶ Whisper tiny/base/small ──▶ guesses ──jiwer.wer vs SENTENCES──▶ table
```

Example of WER by hand: truth "turn the lights off" (4 words), guess "turn lights of" → 1 missing ("the") + 1 wrong ("of") = 2 errors ÷ 4 words = 50%.

## If something goes wrong
- **It takes very long** → each size is downloaded and run on 12 clips. Remove `"small"` from `SIZES` for a quick first run.
- **`ModuleNotFoundError: No module named 'jiwer'`** (or `scipy`) → activate your venv and run the pip line.
- **`ValueError: Voice af_nicole not found`** → your Kokoro voices file is old or damaged. Delete `voice-ai-from-zero/models/voices-v1.0.bin` and run again.
- **WER over 100%** → that's possible: when Whisper adds many extra words (for example hallucinating on noise), errors can exceed the number of correct words.
- **Different numbers each time you change something** → expected. Only compare runs that use the same sentences, voices and noise.

## Try this
1. **Easy:** compare `beam_size=1` with `beam_size=5`. More accurate, or just slower?
   <details><summary>Hint</summary>Change <code>beam_size=1</code> in the transcribe call and run again. With beam size 5, Whisper keeps the 5 best guesses at each step instead of 1. It usually helps a little on hard (noisy) audio, at a clear cost in speed.</details>
2. **Medium:** make the comparison fairer by turning numbers into words before scoring.
   <details><summary>Solution</summary>

   Add above `clean`:
   ```python
   NUMBER_WORDS = {"4": "four", "6": "six", "12": "twelve", "730": "seven thirty"}
   ```
   and change `clean` to:
   ```python
   def clean(text):
       words = re.sub(r"[^a-z0-9' ]", "", text.lower()).split()
       return " ".join(NUMBER_WORDS.get(w, w) for w in words)
   ```
   (`7.30` becomes `730` after punctuation is removed.) The clean WER should drop a lot. Real benchmarks use a full "text normaliser", like the one in OpenAI's Whisper repository, for the same reason.
   </details>
3. **Harder:** test on **real** data: record yourself reading 5 sentences (project 01, one file each), and score the models on your voice.
   <details><summary>Hint</summary>Put your sentences in <code>SENTENCES</code> (in the same order as the files) and replace the Kokoro part with: <code>from faster_whisper import decode_audio</code> and <code>clips = [decode_audio(f"me_{i}.wav") for i in range(5)]</code>. Keep the noisy copies or remove them. Your accent, microphone and room are what really decide which model you need.</details>

## Check yourself
1. Truth: "set an alarm for six" (5 words). Whisper: "set alarm for 6 please". What's the WER?
2. Why does the script use text-to-speech to make the test audio, and what's the weakness of that?
3. What does `25x RT` mean, and is that fast enough for a live assistant?
4. Why does `clean()` remove punctuation and capitals before scoring?

<details><summary>Answers</summary>

1. 1 missing ("an") + 1 wrong ("6" for "six") + 1 extra ("please") = 3 errors ÷ 5 words = 60%.
2. Because then we know exactly what was said (the ground truth) without recording and typing anything, and it's repeatable. The weakness: synthetic voices are cleaner and more regular than real people, so real-world WER is usually higher.
3. 1 second of audio is transcribed in 1/25 of a second (25× faster than real time). Yes, easily: anything well above 1× can keep up.
4. Because we want to score the *words*, not formatting. "Hello," and "hello" mean the same thing and shouldn't count as an error.
</details>

## Learn more (optional)
- jiwer on GitHub: https://github.com/jitsi/jiwer
- Open ASR Leaderboard (WER and speed of many models): search "Hugging Face Open ASR Leaderboard".
- Search YouTube for "word error rate explained".

## Next
→ [22 · Capstone: private meeting assistant](../22-capstone-private-meeting-assistant)
