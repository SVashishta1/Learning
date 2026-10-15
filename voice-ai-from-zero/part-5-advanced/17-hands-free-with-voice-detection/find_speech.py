# Step 1: find where people are speaking in a recording, using Silero VAD (a 2 MB model, very fast).
# Usage: python find_speech.py ../../part-1-sound-basics/01-record-and-play-your-voice/my_voice.wav
import sys
from pathlib import Path

import torch
from faster_whisper import decode_audio          # reads any audio/video file at 16 kHz
from silero_vad import get_speech_timestamps, load_silero_vad

path = sys.argv[1] if len(sys.argv) > 1 else "../../part-1-sound-basics/01-record-and-play-your-voice/my_voice.wav"
if not Path(path).exists():
    sys.exit(f"Can't find {path}. Pass a recording: python find_speech.py my_file.wav")

vad = load_silero_vad()                                   # the model ships inside the pip package
audio = torch.from_numpy(decode_audio(path))              # 16,000 numbers per second, as a PyTorch tensor
parts = get_speech_timestamps(audio, vad, sampling_rate=16000, return_seconds=True,
                              min_silence_duration_ms=300)   # gaps shorter than this don't split speech

total = len(audio) / 16000
spoken = sum(p["end"] - p["start"] for p in parts)
for p in parts:
    print(f"🗣️  {p['start']:6.2f}s → {p['end']:6.2f}s")
print(f"\n{spoken:.1f} s of speech in {total:.1f} s of audio ({spoken / total:.0%})")
