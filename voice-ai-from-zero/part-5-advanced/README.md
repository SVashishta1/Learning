# Part 5 · Advanced

The tricks that make voice apps feel professional.

| # | Project | What you'll learn |
|---|---------|-------------------|
| 17 | [Hands-free with voice detection](17-hands-free-with-voice-detection) | Silero VAD: a tiny model that knows when someone is speaking |
| 18 | [Who spoke when](18-who-spoke-when) | speaker diarization with pyannote: "SPEAKER_1: ..." transcripts |
| 19 | [Real-time assistant with interruptions](19-real-time-assistant-with-interruptions) | streaming audio over WebSockets, answers that start in ~1 s, interrupting the bot mid-sentence |
| 20 | [Clone your own voice](20-clone-your-own-voice) | F5-TTS: speak any text in your voice from a 10-second sample (with consent) |
| 21 | [Measure accuracy](21-measure-accuracy) | Word Error Rate and speed: pick the right Whisper size with numbers |
| 22 | [Capstone: private meeting assistant](22-capstone-private-meeting-assistant) | recording → transcript → summary, decisions, action items, Q&A |

Install once (on top of Part 4):
```bash
pip install silero-vad jiwer scipy
```
Projects 18 and 20 have their own (bigger) installs in their READMEs.
