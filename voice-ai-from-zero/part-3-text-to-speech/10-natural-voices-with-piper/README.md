# 10 · Natural voices with Piper

**What you'll build:** a program that speaks with a **neural voice** that sounds far more natural than project 09. It saves two versions (normal and slow/expressive) and plays them. The voice file is small (~60 MB) and fast enough for a Raspberry Pi.
**Like you're 10:** instead of following pronunciation rules, Piper is a small brain that listened to hours of one real person reading, and learned to sound like them.
**Time:** ~1 h · **Builds on:** [09 · Your computer speaks](../09-your-computer-speaks) · **Needs:** internet once to download a voice (~60 MB)

## Why this matters
Neural TTS is what makes modern assistants, audiobook tools and navigation apps sound human. Piper is popular in home automation (Home Assistant uses it), robots and offline gadgets, because it runs **faster than real time** on a normal CPU: it makes 1 second of speech in much less than 1 second. That speed is what a voice assistant needs.

## What you'll learn
- **Neural TTS**: a neural network that turns text into sound, trained on hours of recordings of one speaker.
- **Phonemes**: the sounds of a language ("cat" = k-æ-t). Piper first converts text to phonemes, then phonemes to audio.
- **ONNX model**: a common file format (`.onnx`) for trained models; the `.onnx.json` file next to it holds the voice's settings.
- **Real-time factor**: how long synthesis takes compared to the length of the audio. Less than 1 = faster than real time.
- **`length_scale` / `noise_scale`**: knobs for speed and expressiveness.

## Before you start
Same install as the rest of Part 3 (skip if done):
```bash
pip install pyttsx3 piper-tts kokoro-onnx soundfile sounddevice numpy
```
- `piper-tts`: the Piper engine (it brings its own phoneme converter, so no extra installs).
- `soundfile` reads the WAV back; `sounddevice` plays it.

No API key needed. You'll download one voice in step 2 below.

## Run it
1. From the course folder:
   ```bash
   cd part-3-text-to-speech/10-natural-voices-with-piper
   ```
2. Download a voice into this folder (once, ~60 MB):
   ```bash
   python -m piper.download_voices en_US-lessac-medium
   ```
   You now have `en_US-lessac-medium.onnx` and `en_US-lessac-medium.onnx.json` here.
3. Make it talk:
   ```bash
   python piper_speak.py "Good morning! Here is your daily summary."
   ```

### What you should see
```
Saved piper.wav: 2.3 s of speech, made in 0.97 s
Saved piper_slow.wav (slower, more expressive)
🔊 Playing piper.wav, then piper_slow.wav...
```
Compare the two numbers on the first line: 2.3 s of speech was made in under 1 second, so it's faster than real time (the first sentence is also the slowest, because the model is warming up). The slow version is longer and a bit more lively. Both sound like a real person, much smoother than project 09.

## How it works
Open `piper_speak.py`.

1. **Check the voice file.** `VOICE = "en_US-lessac-medium.onnx"`. Voice names follow a pattern: language_REGION - speaker name - quality (`x_low`, `low`, `medium`, `high`). If the file isn't there, `sys.exit(...)` tells you how to download it.
2. **Load the voice.** `PiperVoice.load(VOICE)` reads the model and its `.onnx.json` settings (sample rate, phoneme list, default speed).
3. **Synthesize into a WAV file.** `wave.open("piper.wav", "wb")` opens an empty WAV file for writing ("wb" = write binary). `voice.synthesize_wav(text, wav_file)` does all the work:
   - splits the text into sentences;
   - converts each sentence to **phonemes** with eSpeak's rules;
   - the neural network turns the phonemes into audio samples (22,050 per second for this voice);
   - writes them into the file.
4. **Measure speed.** `time.time()` before and after gives `made_in`. `len(audio) / rate` is the length of the speech in seconds.
5. **A second version with settings.** `SynthesisConfig(length_scale=1.3, noise_scale=0.8)`: `length_scale` stretches each sound (1.3 = 30% slower); `noise_scale` adds variation, which sounds more expressive but can get wobbly if too high.
6. **Play both** with `sd.play(...)` and `sd.wait()`, like project 01.

```
"Good morning!" ──▶ sentences ──▶ phonemes (ɡʊd mˈɔːɹnɪŋ) ──▶ neural network ──▶ 22,050 samples/s ──▶ piper.wav ──▶ 🔊
```

## If something goes wrong
- **`First download a voice: ...`** → run the download command from step 2 *inside this folder* (the voice files must be next to `piper_speak.py`).
- **`ModuleNotFoundError: No module named 'piper'`** → activate your venv and re-run the pip line. Note the package name is `piper-tts`, not `piper`.
- **`urllib.error.URLError` or a timeout while downloading** → the voices come from huggingface.co. Check your internet, or download the two files by hand from https://huggingface.co/rhasspy/piper-voices (find `en/en_US/lessac/medium/`) into this folder.
- **`ValueError: Voice '...' did not match pattern`** → check the voice name spelling: `en_US-lessac-medium` (underscore in `en_US`, dashes between parts).
- **You changed `VOICE` but get the old voice or an error** → `VOICE` must be the exact `.onnx` file name, including `.onnx`.

## Try this
1. **Easy:** try a British voice and a voice in another language.
   <details><summary>Hint</summary>Listen to samples at https://rhasspy.github.io/piper-samples/ and pick one. Then e.g. <code>python -m piper.download_voices en_GB-alan-medium</code> and set <code>VOICE = "en_GB-alan-medium.onnx"</code>. For Spanish: <code>es_ES-davefx-medium</code> (and give it Spanish text). Run <code>python -m piper.download_voices</code> with no name to list all voices.</details>
2. **Medium:** find the fastest speed that still sounds clear, and the most expressive `noise_scale` before it sounds strange.
   <details><summary>Hint</summary>Change the numbers in <code>SynthesisConfig(length_scale=1.3, noise_scale=0.8)</code>. Try <code>length_scale</code> 0.7, 0.85, 1.0 and <code>noise_scale</code> 0.3, 0.667 (Piper's usual default), 1.2. Listen to <code>piper_slow.wav</code> each time.</details>
3. **Harder:** use Piper from the command line, with no Python file, and compare its speed with project 09.
   <details><summary>Hint</summary><code>echo "hi there" | python -m piper -m en_US-lessac-medium -f hi.wav</code> (run it in this folder). <code>-m</code> is the voice and <code>-f</code> the output file. Time a long sentence in both projects: Piper is slower than system voices but sounds far better, and is still faster than real time.</details>

## Check yourself
1. What are phonemes, and why does Piper use them?
2. Piper made 4 seconds of speech in 1 second. Is that fast enough for a voice assistant? Why?
3. What is the `.onnx.json` file for?
4. What does `length_scale=1.3` do?

<details><summary>Answers</summary>

1. The individual sounds of a language. English spelling doesn't match pronunciation well ("though", "through"), so converting to phonemes first makes the network's job much easier.
2. Yes: it's 4× faster than real time, so the audio is ready before it would finish playing.
3. It stores the voice's settings: sample rate, phoneme list, and default speed/noise values.
4. It makes every sound 30% longer, so the speech is slower.
</details>

## Learn more (optional)
- Piper on GitHub: https://github.com/OHF-Voice/piper1-gpl
- Listen to all Piper voices: https://rhasspy.github.io/piper-samples/
- Search YouTube for "Piper TTS Home Assistant" to see it in a real product.

## Next
→ [11 · Studio-quality voices with Kokoro](../11-studio-quality-voices-with-kokoro)
