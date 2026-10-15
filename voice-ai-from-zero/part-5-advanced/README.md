# Part 5 · Advanced

The tricks that make voice apps feel professional, and a capstone that uses everything.

| # | Project | What you'll learn | Time |
|---|---------|-------------------|------|
| 17 | [Hands-free with voice detection](17-hands-free-with-voice-detection) | Silero VAD: a tiny model that knows when someone is speaking | 1.5 h |
| 18 | [Who spoke when](18-who-spoke-when) | speaker diarization with pyannote: "SPEAKER_01: ..." transcripts | 2 h |
| 19 | [Real-time assistant with interruptions](19-real-time-assistant-with-interruptions) | streaming audio over WebSockets, answers that start quickly, interrupting the bot mid-sentence | 3 h |
| 20 | [Clone your own voice](20-clone-your-own-voice) | F5-TTS: speak any text in your voice from a 10-second sample (with consent) | 2 h |
| 21 | [Measure accuracy](21-measure-accuracy) | Word Error Rate and speed: pick the right Whisper size with numbers | 1.5 h |
| 22 | [Capstone: private meeting assistant](22-capstone-private-meeting-assistant) | recording → transcript → summary, decisions, action items, Q&A, export | 1 week |

**Install once** (on top of Part 4's packages, in your activated venv):
```bash
pip install silero-vad jiwer scipy websockets
```
- `silero-vad`: voice detection (17, 19); it uses PyTorch, which you already have from Part 2 (otherwise pip installs it).
- `jiwer` + `scipy`: Word Error Rate and resampling (21).
- `websockets`: lets `uvicorn` handle WebSocket connections (19).

**Bigger, separate installs** (explained in their READMEs): project 18 needs `pip install pyannote.audio` and a free Hugging Face token; project 20 needs `pip install f5-tts` (~2–3 GB with its dependencies). If either causes version conflicts, give it its own fresh virtual environment.

Projects 19 and 22 also need Ollama running (see the [Part 4 README](../part-4-voice-apps/README.md)).

Start here → [17 · Hands-free with voice detection](17-hands-free-with-voice-detection)
