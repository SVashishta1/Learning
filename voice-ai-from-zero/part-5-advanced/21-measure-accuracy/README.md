# 21 · Measure accuracy

**What it does:** answers "which Whisper size is good enough for me?" with numbers instead of guesses. It tests `tiny`, `base` and `small` on clean and noisy speech and prints:

```
model    audio     WER        speed
tiny     clean    6.2%      25.3x RT
tiny     noisy   18.5%      22.1x RT
         ✗ She sells sea shells by the sea shore on sunny Saturdays.
base     clean    1.5%      12.0x RT
...
```
(Your numbers will differ.)

## The two numbers that matter
- **WER (Word Error Rate)** = (wrong + missing + extra words) ÷ number of correct words. 0% is perfect; under 5% is very good. It's the standard score every speech-recognition paper reports.
  Careful: Whisper often writes `12` for "twelve" or `7:30` for "seven thirty". That counts as an error here, though it isn't really one. Serious benchmarks convert numbers before comparing.
- **Speed ×RT (real-time)**: `10x RT` means 1 minute of audio is transcribed in 6 seconds. For a live assistant you need well above `1x`.

## Run it
```bash
cd part-5-advanced/21-measure-accuracy
python benchmark.py
```
No recording needed: Kokoro reads known sentences, so we know the right answers. (Copy the Kokoro files from project 11 to skip the download.)

## Try this
1. Add `"medium"` and `"large-v3-turbo"` to `SIZES` (big downloads). Is the accuracy worth the time?
2. Use **real** test data: record yourself reading 5 sentences, and put the files + true text in the lists. Your accent and microphone are what matter.
3. Compare `beam_size=1` vs `beam_size=5`: more accurate or just slower?
