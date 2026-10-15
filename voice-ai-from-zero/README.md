# Voice AI from Zero 🎙️

**22 small projects** that take you from "record my voice" to a fully **private, local voice assistant**, using only **free, open-source models that run on your own computer** (or even inside your web browser). No API keys and no cloud: your voice never leaves your machine.

Same style as [`ai-from-zero`](../ai-from-zero): one short file per project, plain-English comments, very little theory. Every project README follows the same pattern: what you'll build → why it matters → install → run it (with real sample output) → how the code works → fixes for common problems → exercises with hints and solutions → a short self-check.

**Before this course:** finish **AI from Zero** [00 · Start here](../ai-from-zero/00-start-here) and Parts 1–4 (Python basics, APIs with FastAPI, chatbots). You should be comfortable running `python file.py` in a terminal and using a virtual environment.

| Part | You'll build | Time |
|------|-------------|------|
| [1 · Sound basics](part-1-sound-basics) | record, play and *see* your voice; a recorder in the browser | 3 h |
| [2 · Speech to text](part-2-speech-to-text) | Whisper transcription: files, live microphone, subtitles, translation, **Whisper inside the browser** | 1 week |
| [3 · Text to speech](part-3-text-to-speech) | your computer talks: system voices, Piper, Kokoro, browser voices | 4 h |
| [4 · Voice apps](part-4-voice-apps) | voice notes, voice commands, a talking local AI, a voice-assistant web app | 1 week |
| [5 · Advanced](part-5-advanced) | voice detection, who-spoke-when, real-time streaming with interruptions, voice cloning (with consent), measuring accuracy, a private meeting assistant | 2 weeks |

**Total: about 4–5 weeks at 1 hour a day.**

## The open-source models you'll use
| Model | Job | Runs where | Size |
|-------|-----|-----------|------|
| **Whisper** (OpenAI, MIT licence) via `openai-whisper` and `faster-whisper` | speech → text, 99 languages, translation | your computer | 75 MB (tiny) – 3 GB (large) |
| **Whisper in the browser** (transformers.js) | speech → text with no server at all | Chrome/Edge | 40–500 MB |
| **Piper** | text → speech, fast, 40+ languages | your computer, even a Raspberry Pi | ~60 MB per voice |
| **Kokoro-82M** (Apache licence) | text → speech, very natural | computer or browser | ~340 MB (~90 MB in the browser) |
| **Silero VAD** | "is someone speaking right now?" | your computer | 2 MB |
| **pyannote** | who spoke when | your computer | ~30 MB |
| **F5-TTS** | voice cloning from a short sample | your computer (GPU recommended) | ~1.3 GB |
| **Llama / Qwen via Ollama** | the "brain" of the assistant | your computer | ~2 GB |

## Setup (once)
Do these steps once, in order. They take 20–40 minutes, mostly waiting for downloads.

### 1. Check your computer
- **Any recent Windows 10/11, macOS or Linux laptop works.** 8 GB of RAM is enough for everything except comfortable use of the LLM in Parts 4–5, where 16 GB is nicer. A graphics card is optional (it only speeds up projects 18 and 20).
- **Free disk space: plan for about 15 GB** (see the table in step 7).
- A microphone (the built-in one is fine) and **headphones or earphones** (see step 6).

### 2. Install Python 3.12
Use **Python 3.12**. Some audio packages don't support 3.13 yet; 3.10 and 3.11 also work.
- **Windows:** `winget install Python.Python.3.12` in a terminal, or download it from https://www.python.org/downloads/ and tick **"Add python.exe to PATH"** in the installer.
- **Mac:** `brew install python@3.12` (install Homebrew first from https://brew.sh if you don't have it).
- **Linux (Ubuntu/Debian):** `sudo apt install python3.12 python3.12-venv` (Ubuntu 24.04 already has it; on older versions use your distribution's newest Python 3.10–3.12).

Check: `python --version` (Windows: `py -3.12 --version`) should print `Python 3.12.x`.

### 3. Install ffmpeg and system audio libraries
**ffmpeg** converts between audio and video formats. Whisper and F5-TTS use it to read files.
- **Windows:** `winget install ffmpeg`
- **Mac:** `brew install ffmpeg`
- **Linux:** `sudo apt install ffmpeg libportaudio2 espeak-ng` (PortAudio is the microphone/speaker library `sounddevice` uses; eSpeak NG is the system voice for projects 09 and 14. Windows and Mac already have both.)

**Close and reopen your terminal**, then check: `ffmpeg -version` prints a version number.

### 4. Make a virtual environment for the course
A **virtual environment** (venv) is a private folder of Python packages for this course, so nothing clashes with other projects. Open a terminal **in the `voice-ai-from-zero` folder** (every `cd ...` command in the lessons starts from here):
- **Windows (PowerShell or Command Prompt):**
  ```bash
  py -3.12 -m venv .venv
  .venv\Scripts\activate
  ```
  If PowerShell says "running scripts is disabled", run `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` once, then activate again.
- **Mac / Linux:**
  ```bash
  python3.12 -m venv .venv
  source .venv/bin/activate
  ```
Your prompt now starts with `(.venv)`. **Activate it every time you open a new terminal** for this course. Then update pip:
```bash
python -m pip install --upgrade pip
```

### 5. Install the packages
Each part's README (and each project) gives its `pip install` line; run them as you reach each part. Or install everything for Parts 1–5 now:
```bash
pip install sounddevice soundfile numpy matplotlib openai-whisper faster-whisper "av<19" pyttsx3 piper-tts kokoro-onnx fastapi uvicorn python-multipart httpx silero-vad jiwer scipy websockets
```
Notes:
- Keep the quotes around `"av<19"`: it means "any version below 19" (version 19 breaks faster-whisper 1.2).
- **Linux without an NVIDIA graphics card:** install the small CPU-only PyTorch *first*, which saves about 4 GB: `pip install torch torchaudio --index-url https://download.pytorch.org/whl/cpu`, then the line above.
- Projects 18 (`pyannote.audio`) and 20 (`f5-tts`) have bigger installs, explained in their READMEs.
- Projects 15, 16, 19 and 22 also need **Ollama** (a free app that runs the LLM): see the [Part 4 README](part-4-voice-apps/README.md).

### 6. Microphone permissions and headphones
The first time a program uses the microphone, your system may block it silently (you'll record silence).
- **Windows:** Settings → Privacy & security → Microphone → turn on **Microphone access** and **Let desktop apps access your microphone**.
- **Mac:** System Settings → Privacy & Security → Microphone → turn on your terminal app (Terminal, iTerm or VS Code) and your browser. Restart the app after changing it.
- **Linux:** usually nothing to do. Check the input device and level in Settings → Sound, or with `pavucontrol`.
- **Browser projects (03, 07, 12, 13, 16, 19, 22):** click **Allow** when asked. If you clicked Block, click the 🔒 icon in the address bar → Microphone → Allow, and reload. Browsers only allow the microphone on `http://localhost` or `https://` pages.
- **Test it:** after installing Part 1, run `python -m sounddevice` to list your devices (`>` marks the default microphone, `<` the default speaker), then do [project 01](part-1-sound-basics/01-record-and-play-your-voice).

**Use headphones or earphones** for the projects that listen and talk at the same time (14, 15, 16, 19). With speakers, the microphone hears the computer's own voice and it starts answering itself or interrupting itself.

### 7. Where downloaded models are stored, and disk space
Models download automatically the first time a project needs them, then they're reused. You can delete these folders any time to free space (they'll download again if needed). `~` means your home folder (Windows: `C:\Users\<you>`).

| What | Where it's stored | Size |
|------|-------------------|------|
| Python packages (incl. PyTorch) | `voice-ai-from-zero/.venv/` | ~3 GB (Windows/Mac or Linux CPU-only), up to ~7 GB with Linux CUDA PyTorch |
| Whisper for `openai-whisper` (project 04) | `~/.cache/whisper/` | 140 MB for `base` |
| faster-whisper models (tiny, base, small) | `~/.cache/huggingface/hub/` | ~0.7 GB |
| Kokoro voice model (projects 11, 15, 16, 19, 21) | `voice-ai-from-zero/models/` | ~340 MB |
| Piper voice (project 10) | project 10's folder | ~60 MB per voice |
| Browser models (projects 07, 12) | your browser's cache | ~0.2–0.6 GB |
| Ollama LLM (`llama3.2:3b`) | Ollama's folder (`~/.ollama/models`) | ~2 GB |
| pyannote (project 18) + its packages | `~/.cache/huggingface/hub/` + venv | ~1 GB |
| F5-TTS (project 20) + its packages | `~/.cache/huggingface/hub/` + venv | ~3 GB |
| **Total** | | **~11–15 GB** |

Large files are listed in `.gitignore`, so they're never committed to git.

## How to work through a project
1. Activate the venv, `cd` into the project folder (the README shows the exact command), and run the command in **Run it**.
2. Compare your output with **What you should see**.
3. Read **How it works** with the code open next to it.
4. Do the **Try this** exercises (open the hints only when stuck), then answer **Check yourself**.

If something breaks, look at the project's **If something goes wrong** section first. Most problems are one of: the venv isn't active (`ModuleNotFoundError`), you're in the wrong folder (`file not found`), the microphone is blocked (silent recording), or Ollama isn't running.

Start here → [Part 1 · Sound basics](part-1-sound-basics)

**When you finish:** go deeper with [`../ai-engineer-journey`](../ai-engineer-journey).
