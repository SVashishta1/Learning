# Voice AI from Zero 🎙️

**22 small projects** that take you from "record my voice" to a fully **private, local voice assistant**, using only **free, open-source models that run on your own computer** (or even inside your web browser). No API keys and no cloud: your voice never leaves your machine.

Same style as `ai-from-zero`: one short file per project, plain-English comments, very little theory. Finish **AI from Zero Parts 1–4** first (Python, APIs, chatbots).

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
| **Whisper in the browser** (transformers.js) | speech → text with no server at all | Chrome/Edge | 40–150 MB |
| **Piper** | text → speech, fast, 40+ languages | your computer, even a Raspberry Pi | ~60 MB per voice |
| **Kokoro-82M** (Apache licence) | text → speech, very natural | computer or browser | ~330 MB |
| **Silero VAD** | "is someone speaking right now?" | your computer | 2 MB |
| **pyannote** | who spoke when | your computer | ~30 MB |
| **F5-TTS** | voice cloning from a short sample | your computer (GPU recommended) | ~1.3 GB |
| **Llama / Qwen via Ollama** | the "brain" of the assistant | your computer | ~2 GB |

## Setup (once)
1. Install **ffmpeg** (audio converter that Whisper uses):
   - Windows: `winget install ffmpeg` · Mac: `brew install ffmpeg` · Linux: `sudo apt install ffmpeg`
2. Make a virtual environment, as in `ai-from-zero/00-start-here`. **Use Python 3.10, 3.11 or 3.12** (some audio packages don't support 3.13 yet).
3. Each part's README lists its `pip install` line.
4. A headset or earphones help: they stop your computer hearing itself.
