# 01 · Record and play your voice

**What you'll build:** a tiny Python program that records 5 seconds from your microphone, plays it back to you, and saves it as `my_voice.wav`. You'll use that file in many later projects.
**Like you're 10:** a microphone turns your voice into a very long list of numbers. We catch the list, play it back, and save it.
**Time:** ~45 min · **Builds on:** nothing (just the course [setup](../../README.md#setup-once)) · **Needs:** a microphone and speakers or headphones

## Why this matters
Every voice product starts here: Siri, Alexa, Zoom captions and phone-call bots all record sound as numbers before any AI sees it. Knowing what a recording *is* (numbers, a sample rate, channels) helps you fix the most common voice-AI bugs, which are usually "wrong format" bugs, not "bad AI" bugs.

## What you'll learn
- **Sample**: one number that says how far the microphone was pushed at one instant, between -1 and 1.
- **Sample rate**: how many samples per second. 16,000 (16 kHz) is what speech models like Whisper expect.
- **Channels**: 1 channel = mono (one microphone), 2 = stereo. Speech AI uses mono.
- **WAV file**: the simplest audio file: a short header and then the numbers, saved as they are.

## Before you start
Activate your virtual environment (see the [course setup](../../README.md#setup-once)), then install the Part 1 packages:
```bash
pip install sounddevice soundfile numpy matplotlib
```
- `sounddevice`: talks to your microphone and speakers.
- `soundfile`: reads and writes audio files like `.wav`.
- `numpy`: fast lists of numbers (your recording is one).
- `matplotlib`: draws charts (used in project 02).

**Linux only:** `sounddevice` needs the PortAudio library: `sudo apt install libportaudio2`.

No API key needed. Nothing is downloaded.

## Run it
1. Open a terminal in the course folder (`voice-ai-from-zero`) and go to this project:
   ```bash
   cd part-1-sound-basics/01-record-and-play-your-voice
   ```
2. Run the program, and talk for 5 seconds as soon as you see "Recording":
   ```bash
   python record.py
   ```
3. Listen to the playback. Then open `my_voice.wav` (it's in this folder) in any music player.

### What you should see
```
🎙️  Recording for 5 seconds... say something!
✅ Done. Playing it back...
💾 Saved my_voice.wav. It's 80,000 numbers; the loudest one is 0.55 (1.0 = max).
First 8 numbers of your voice: [ 0.008   0.0004 -0.0011 -0.0021  0.0006  0.0003  0.0028  0.0013]
```
Look at three things:
- **80,000 numbers**: 5 seconds × 16,000 per second. The maths works.
- **The loudest one**: 0.1 to 0.7 is good. Near 0.00 means the microphone heard nothing (see below). 1.00 means you were too loud and the sound got "clipped".
- **The first 8 numbers** are tiny: that's the quiet moment before you started talking.

## How it works
Open `record.py` and follow along.

1. **Two settings at the top.** `SAMPLE_RATE = 16000` and `SECONDS = 5`. So the program needs `5 × 16000 = 80,000` samples.
2. **`sd.rec(...)` starts recording.** It asks the microphone for `int(SECONDS * SAMPLE_RATE)` samples, with `channels=1` (mono) and `dtype="float32"` (decimal numbers between -1 and 1). It returns straight away and keeps recording in the background.
3. **`sd.wait()`** pauses the program until the 5 seconds are over. Without it, the next line would run while you're still talking.
4. **`audio` is a numpy table** with 80,000 rows and 1 column (one column per channel). That's why the last line uses `audio[:8, 0]`: "the first 8 rows of column 0".
5. **`sd.play(audio, SAMPLE_RATE)`** sends the same numbers to your speakers. The sample rate tells the speakers how fast to play them. Play them at 32,000 per second and you'd sound like a chipmunk.
6. **`sf.write("my_voice.wav", audio, SAMPLE_RATE)`** saves the numbers plus a small header (the sample rate and channel count), so any player can open it.
7. **`abs(audio).max()`** finds the biggest number, ignoring the minus sign. It's a quick "did it hear me?" check.

```
your voice ──▶ microphone ──▶ 16,000 numbers per second ──▶ audio (numpy) ──┬──▶ speakers
                                                                             └──▶ my_voice.wav
```

## If something goes wrong
- **`ModuleNotFoundError: No module named 'sounddevice'`** → your virtual environment isn't active, or you skipped the install. Activate it and re-run the `pip install` line above.
- **`OSError: PortAudio library not found`** (Linux) → run `sudo apt install libportaudio2`, then try again.
- **"the loudest one is 0.00" / the playback is silent** → the computer blocked the microphone or used the wrong one.
  - Mac: System Settings → Privacy & Security → Microphone → turn on your terminal app (or VS Code), then restart it.
  - Windows: Settings → Privacy & security → Microphone → turn on "Let desktop apps access your microphone".
  - Run `python -m sounddevice` to list devices. The one marked `>` is the default input. Change the default in your system sound settings, or add `sd.default.device = 1` (your microphone's number) after the imports.
- **`PortAudioError: Invalid sample rate`** → a few microphones refuse 16,000. Set `SAMPLE_RATE = 44100` or `48000`; later projects convert it for Whisper automatically.
- **You hear nothing on playback, but the loudest number looks fine** → check your speaker volume and the default output device (the one marked `<` in `python -m sounddevice`).

## Try this
1. **Easy:** record for 10 seconds instead of 5.
   <details><summary>Hint</summary>Change <code>SECONDS = 5</code> to <code>SECONDS = 10</code>. The message and the number count update by themselves: you should now see 160,000 numbers.</details>
2. **Medium:** compare sound quality. Set `SAMPLE_RATE` to 8000 (old telephone quality), record, listen; then 44100 (CD quality). Can you hear the difference?
   <details><summary>Hint</summary>At 8,000 per second, "s" and "f" sound dull and muffled, because high pitches need many samples per second to be captured. Speech models use 16,000 as a good middle ground. Put it back to 16000 when you're done, because later projects expect it.</details>
3. **Harder:** save each recording with the date and time in its name, so you don't overwrite the last one (for example `voice_2026-10-15_09-30-12.wav`).
   <details><summary>Solution</summary>

   ```python
   from datetime import datetime
   name = datetime.now().strftime("voice_%Y-%m-%d_%H-%M-%S.wav")
   sf.write(name, audio, SAMPLE_RATE)
   print("Saved", name)
   ```
   Put the import at the top and replace the `sf.write(...)` line. Keep one recording named `my_voice.wav` too, because later projects look for that name.
   </details>

## Check yourself
1. You record 3 seconds at 16,000 samples per second. How many numbers do you get?
2. What would happen if you saved at 16,000 but played the numbers back at 8,000 per second?
3. Why does the program need `sd.wait()` after `sd.rec(...)`?
4. Your recording's loudest number is 0.003. What's the most likely problem?

<details><summary>Answers</summary>

1. 3 × 16,000 = 48,000 numbers.
2. It would take twice as long and sound deep and slow, because each second of numbers now takes two seconds to play.
3. `sd.rec` starts recording in the background and returns immediately. `sd.wait()` waits until the recording is finished, so you don't play or save an empty recording.
4. The microphone is blocked (permission) or the wrong input device is selected, so it only recorded faint noise.
</details>

## Learn more (optional)
- sounddevice examples: https://python-sounddevice.readthedocs.io/en/latest/examples.html
- What is sample rate? Search YouTube for "sample rate and bit depth explained".

## Next
→ [02 · See your voice](../02-see-your-voice)
