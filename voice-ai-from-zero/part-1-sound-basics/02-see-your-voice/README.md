# 02 · See your voice

**What you'll build:** a program that draws your recording as two pictures, a **wave** and a **spectrogram**, and prints a little loudness bar so you can spot speech and silence.
**Like you're 10:** the wave shows *how loud*, the spectrogram shows *how high or low*. Together they're a photo of your voice.
**Time:** ~1 h · **Builds on:** [01 · Record and play your voice](../01-record-and-play-your-voice) · **Needs:** nothing extra (uses `my_voice.wav` from project 01)

## Why this matters
Speech AI doesn't "hear". Whisper turns audio into a spectrogram-like picture (a **log-Mel spectrogram**) and reads it a bit like an image model reads a photo. When transcription goes wrong, audio engineers look at these two pictures first: is it too quiet, clipped, noisy, or silent?

## What you'll learn
- **Waveform**: the samples drawn over time. Tall = loud, flat = silence.
- **Spectrogram**: a heat-map with time going right, pitch going up, and brightness showing how loud each pitch is.
- **Frequency (Hz)**: how many times per second the air vibrates. Low voice ≈ 100 Hz, "sss" ≈ 5,000+ Hz.
- **RMS loudness**: the average size of the numbers in a short slice, a simple measure of loudness.

## Before you start
Same packages as project 01 (skip if you already installed them):
```bash
pip install sounddevice soundfile numpy matplotlib
```
- `soundfile` reads the WAV file, `numpy` does the maths, `matplotlib` draws the pictures.

You need `my_voice.wav` from project 01. No API key needed.

## Run it
1. From the course folder:
   ```bash
   cd part-1-sound-basics/02-see-your-voice
   ```
2. Draw your project 01 recording (it's found automatically):
   ```bash
   python see_voice.py
   ```
   Or draw any other audio file: `python see_voice.py path/to/file.wav`
3. Open `my_voice.png`, which is now in this folder.

### What you should see
```
Saved my_voice.png  (5.0 s of audio at 16000 samples/second)
Loudness every 0.1 s:           ▂▄█ ▆▄▃ ▅▄▂▁▃▅▂▄▁▂▃▃▂▂▄▆▁     ▁▇▅▅▅▃▆▆▄▂
```
Each character is 0.1 seconds. Spaces are silence: here the first second is quiet, then speech, a short pause around 3.5 s, and more speech.

`my_voice.png` looks like this (your shapes will differ):
- **Top (the wave):** a flat line where you were silent, then bursts where you spoke. Each burst is roughly one word or syllable.
- **Bottom (the spectrogram):** dark = quiet, bright yellow/orange = loud. Voiced sounds ("a", "m") show stacked horizontal stripes near the bottom; "s" and "t" show bright smudges high up.

## How it works
Open `see_voice.py`.

1. **Pick the file.** `sys.argv` is the list of words you typed after `python`. If you gave a file name, `sys.argv[1]` is it; otherwise it uses project 01's `my_voice.wav`. If the file doesn't exist, `sys.exit(...)` stops with a friendly message.
2. **Read it.** `sf.read(path)` returns `audio` (the numbers) and `rate` (samples per second). If the file is stereo, `audio.mean(axis=1)` averages the two channels into one.
3. **Make a time axis.** `np.arange(len(audio)) / rate` turns sample numbers 0, 1, 2... into seconds 0, 0.0000625, 0.000125...
4. **Draw the wave.** `plt.subplots(2, 1)` makes two charts on top of each other. `top.plot(seconds, audio)` draws every sample.
5. **Draw the spectrogram.** `bottom.specgram(...)` cuts the audio into small windows of 512 samples (32 ms), measures how strong every pitch is in each window (with a maths trick called the **Fourier transform**), and colours it. `noverlap=384` makes windows overlap so the picture is smooth.
6. **Save.** `plt.savefig("my_voice.png")` writes the picture.
7. **Loudness bar.** It cuts the audio into 0.1 s slices (`rate // 10` samples each), and for each slice computes **RMS** = square every number, average them, take the square root. Then it picks a character from `" ▁▂▃▄▅▆▇█"`: louder slice, taller bar.

```
my_voice.wav ──▶ numbers ──┬──▶ wave picture        (loudness over time)
                           ├──▶ spectrogram picture (pitch over time)
                           └──▶ loudness bar        (RMS every 0.1 s)
```

## If something goes wrong
- **`Can't find ../01-record-and-play-your-voice/my_voice.wav`** → run project 01 first, or pass a file name.
- **`ModuleNotFoundError: No module named 'matplotlib'`** → activate your venv and re-run the `pip install` line above.
- **`LibsndfileError: Format not recognised`** with an `.mp3`/`.m4a` → `soundfile` reads WAV, FLAC and OGG. Convert first: `ffmpeg -i input.m4a output.wav`.
- **The wave is a flat line** → the recording is silent. Go back to project 01's "If something goes wrong".
- **The loudness bar is all `█`** → you were very loud or close to the microphone. Re-record a bit further away.

## Try this
1. **Easy:** record (project 01) yourself saying "sssss" and then "mmmmm". Where does each one show up in the spectrogram, high or low?
   <details><summary>Hint</summary>"sss" is a hiss: a bright smudge high up (4,000–8,000 Hz) with no stripes. "mmm" is a hum: bright stripes near the bottom (100–1,000 Hz). Whisper uses exactly these patterns to tell sounds apart.</details>
2. **Medium:** whistle a rising note, then look for a bright line climbing in the spectrogram. Then make the picture zoom in on 0–4,000 Hz, where most speech lives.
   <details><summary>Hint</summary>After the <code>bottom.specgram(...)</code> line, add <code>bottom.set_ylim(0, 4000)</code>.</details>
3. **Harder:** print how many seconds of the recording are speech, using the loudness numbers you already have.
   <details><summary>Solution</summary>

   ```python
   speaking = sum(1 for l in loudness if l > 0.02)     # slices louder than a whisper
   print(f"Speech: about {speaking / 10:.1f} s of {len(audio) / rate:.1f} s")
   ```
   Add it at the end. `0.02` is a guess: adjust it for your microphone. This "loudness check" is the same trick project 05 uses to find pauses, and project 17 replaces it with a small AI model.
   </details>

## Check yourself
1. In the wave picture, what does a flat line mean?
2. In the spectrogram, which direction is time and which is pitch?
3. Why do the "s" sounds appear near the top of the spectrogram?
4. What does RMS measure, in plain words?

<details><summary>Answers</summary>

1. Silence: the samples are all close to 0.
2. Time goes left to right; pitch (frequency) goes bottom (low) to top (high).
3. "s" is made of very fast vibrations (high frequencies, thousands per second), and the spectrogram puts high frequencies at the top.
4. The typical size of the numbers in a slice, ignoring the sign, which is how loud that slice is.
</details>

## Learn more (optional)
- Search YouTube for "what is a spectrogram" (short visual explanations).
- matplotlib `specgram` docs: https://matplotlib.org/stable/api/_as_gen/matplotlib.pyplot.specgram.html

## Next
→ [03 · Voice recorder in the browser](../03-voice-recorder-in-the-browser)
