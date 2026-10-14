# Turn any recording (wav, mp3, m4a, mp4...) into text with OpenAI's open-source Whisper. Runs 100% on your computer.
# Usage: python transcribe.py ../../part-1-sound-basics/01-record-and-play-your-voice/my_voice.wav
import sys
import time

import whisper

path = sys.argv[1] if len(sys.argv) > 1 else "../../part-1-sound-basics/01-record-and-play-your-voice/my_voice.wav"
size = sys.argv[2] if len(sys.argv) > 2 else "base"          # tiny, base, small, medium, large-v3, turbo

print(f"Loading the Whisper '{size}' model (downloads once)...")
model = whisper.load_model(size)

start = time.time()
result = model.transcribe(path)               # that's it: audio in, text out
print(f"\n📝 {result['text'].strip()}\n")
print(f"Language: {result['language']} | took {time.time() - start:.1f} s")

# Whisper also tells you WHEN each sentence was said
for seg in result["segments"]:
    print(f"  [{seg['start']:5.1f}s → {seg['end']:5.1f}s] {seg['text'].strip()}")
