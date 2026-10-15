# 04 · Transcribe a file with Whisper

**What you'll build:** a program that turns any recording (wav, mp3, m4a, even a video) into text, tells you the language, and gives a time stamp for each sentence. It uses **OpenAI's open-source Whisper** model on your own computer.
**Like you're 10:** you give Whisper a sound file, it writes down what was said, like a very fast typist who knows 99 languages.
**Time:** ~1 h · **Builds on:** [03 · Voice recorder in the browser](../../part-1-sound-basics/03-voice-recorder-in-the-browser) (and `my_voice.wav` from [01](../../part-1-sound-basics/01-record-and-play-your-voice)) · **Needs:** ffmpeg, ~2.5 GB free disk for PyTorch + the model

## Why this matters
Speech-to-text (also called **ASR**, automatic speech recognition) is behind meeting notes, video captions, call-centre analytics and every voice assistant. Whisper is the open model most companies and hobbyists start with, because it's free (MIT licence), accurate, and works offline. Ten years ago this was a research problem; now it's two lines of Python.

## What you'll learn
- **Model**: a file of learned numbers (the "weights") plus code that uses them. `whisper.load_model("base")` loads one into memory.
- **Model size**: bigger models (more weights) make fewer mistakes but are slower. `tiny` → `base` → `small` → `medium` → `large-v3`.
- **Inference**: using a trained model to get an answer. `model.transcribe(...)` is inference.
- **Segments**: Whisper splits the text into short pieces, each with a start and end time.

## Before you start
1. ffmpeg must be installed (see the [course setup](../../README.md#setup-once)). Whisper uses it to open mp3, m4a, mp4 and other files.
2. Activate your venv and install the Part 2 packages (this downloads PyTorch, so it can take a few minutes):
   ```bash
   pip install openai-whisper faster-whisper "av<19" sounddevice soundfile numpy
   ```
   - `openai-whisper`: OpenAI's own Whisper package (used in this project). It brings **PyTorch**, the maths engine that runs the model.
   - `faster-whisper`: a faster version of Whisper, used from project 05 on. `"av<19"` pins the audio library it uses, because version 19 broke it.
   - `sounddevice`, `soundfile`, `numpy`: microphone, audio files and numbers, as in Part 1.
3. No API key needed. The first run downloads the model once (base = 140 MB) into `~/.cache/whisper` (Windows: `C:\Users\<you>\.cache\whisper`).

## Run it
1. From the course folder:
   ```bash
   cd part-2-speech-to-text/04-transcribe-a-file-with-whisper
   ```
2. Transcribe your recording from project 01 (used automatically when you give no file):
   ```bash
   python transcribe.py
   ```
3. Transcribe any other file, and optionally choose a model size as a second word:
   ```bash
   python transcribe.py "my podcast.mp3" small
   ```
   Put quotes around file names that contain spaces.

### What you should see
Here we transcribed a 12-second test recording with two sentences and a pause:
```
Loading the Whisper 'base' model (downloads once)...
100%|█████████████████████████████████████| 139M/139M [00:09<00:00, 15.2MiB/s]
.../whisper/transcribe.py:132: UserWarning: FP16 is not supported on CPU; using FP32 instead
  warnings.warn("FP16 is not supported on CPU; using FP32 instead")

📝 The quick brown fox jumps over the lazy dog. Machine learning is fun. Hello, I am speaking from your own computer. No internet needed.

Language: en | took 2.1 s
  [  1.0s →   5.6s] The quick brown fox jumps over the lazy dog. Machine learning is fun.
  [  7.7s →  11.4s] Hello, I am speaking from your own computer. No internet needed.
```
- The progress bar appears only the first time (the download).
- The **FP16 warning is normal** on a computer without an NVIDIA graphics card. It just means "using normal-precision numbers". Ignore it.
- Check the **segments**: the gap from 5.6 s to 7.7 s is a pause in the speech.
- `took 2.1 s` depends on your computer and the length of the audio.

## How it works
Open `transcribe.py`.

1. **Read the command line.** `sys.argv[1]` is the file (default: project 01's `my_voice.wav`), `sys.argv[2]` the model size (default `base`). If the file doesn't exist, it stops with a clear message.
2. **Load the model.** `whisper.load_model(size)` downloads the weights the first time and keeps them in `~/.cache/whisper`. Loading takes a few seconds, so real apps load once and reuse the model many times.
3. **Transcribe.** `model.transcribe(path)` does everything:
   - runs `ffmpeg` to convert the file to 16,000 samples per second, mono (exactly what you recorded in project 01);
   - cuts it into 30-second windows;
   - turns each window into a **log-Mel spectrogram** (the picture from project 02);
   - the **encoder** (part of the model) reads the picture, and the **decoder** writes text one small piece (a **token**) at a time, like autocomplete.
4. **Time it.** `time.time()` before and after gives the seconds taken.
5. **Print the result.** `result` is a Python dictionary: `result["text"]` (everything), `result["language"]` (a code like `en`, `es`, `hi`) and `result["segments"]` (a list, each with `start`, `end`, `text`). `:5.1f` means "5 characters wide, 1 decimal".

```
my_voice.wav ──ffmpeg──▶ 16 kHz numbers ──▶ spectrogram ──▶ encoder ──▶ decoder ──▶ "The quick brown fox..."
                                                                                     + language + segments
```

## If something goes wrong
- **`FileNotFoundError: [WinError 2] The system cannot find the file specified`** or **`No such file or directory: 'ffmpeg'`** → ffmpeg isn't installed or the terminal can't find it. Install it (course setup), then **close and reopen** the terminal. Check with `ffmpeg -version`.
- **`ModuleNotFoundError: No module named 'whisper'`** → activate your venv and run the pip line. Be careful: the package is `openai-whisper`; `pip install whisper` installs an unrelated package. If you did that, run `pip uninstall whisper` and then the correct line.
- **The download stops or is very slow** → run it again: it resumes. Try `tiny` (75 MB) first.
- **The text is empty or nonsense ("Thank you." on a silent file)** → the recording is silent or very noisy. Whisper sometimes "hallucinates" a short phrase on silence. Check the file with project 02.
- **It's very slow** → use a smaller model (`tiny` or `base`). Project 05's faster-whisper is about 4× faster.

## Try this
1. **Easy:** transcribe the same file with `tiny` and with `small`. Compare the time taken and the mistakes.
   <details><summary>Hint</summary><code>python transcribe.py my_voice.wav tiny</code> then <code>python transcribe.py my_voice.wav small</code> (with the full path to your file). Expect <code>small</code> to be around 3–4× slower but to get names and rare words right more often.</details>
2. **Medium:** record a sentence in another language you know (project 01) and transcribe it. Then force the language: change the transcribe line to `model.transcribe(path, language="es")` (use your language's code).
   <details><summary>Hint</summary>Whisper guesses the language from the first 30 seconds. On short or mixed recordings the guess can be wrong; giving <code>language=</code> fixes that and is slightly faster. Codes: <code>en</code>, <code>es</code>, <code>fr</code>, <code>de</code>, <code>hi</code>, <code>pt</code>, <code>zh</code>, ...</details>
3. **Harder:** save the transcript to a text file named after the audio (`my_voice.txt`).
   <details><summary>Solution</summary>

   Add at the end:
   ```python
   out = Path(path).with_suffix(".txt")
   out.write_text(result["text"].strip() + "\n", encoding="utf-8")
   print("Saved", out)
   ```
   `with_suffix(".txt")` swaps the file extension. `encoding="utf-8"` matters for non-English text on Windows.
   </details>

## Check yourself
1. Why does the program load the model once, before transcribing, instead of inside a loop?
2. What does ffmpeg do in this project?
3. You need very accurate notes from a long lecture and don't mind waiting. Which size do you pick, and why?
4. What is a "segment"?

<details><summary>Answers</summary>

1. Loading takes seconds and lots of memory. Load once, then reuse it for every file.
2. It opens any audio/video format and converts it to 16 kHz mono numbers, the format Whisper needs.
3. A bigger one (`small` or `medium`, or `large-v3` with a GPU): more weights = fewer mistakes, at the cost of speed.
4. A short piece of the transcript (often a sentence) with its start and end time.
</details>

## Learn more (optional)
- Whisper on GitHub (model sizes, languages): https://github.com/openai/whisper
- OpenAI's Whisper announcement: https://openai.com/index/whisper/
- Search YouTube for "how does OpenAI Whisper work".

## Next
→ [05 · Faster Whisper + live microphone](../05-faster-whisper-live-microphone)
