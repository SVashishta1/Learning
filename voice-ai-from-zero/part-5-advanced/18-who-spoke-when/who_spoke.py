# Who spoke when: pyannote finds the speakers, Whisper finds the words, we join the two.
# Usage: python who_spoke.py meeting.mp3
# Output: transcript with "SPEAKER_00: ..." lines -> transcript.txt
import os
import sys
from pathlib import Path

import torch
from faster_whisper import WhisperModel, decode_audio
from pyannote.audio import Pipeline

file = sys.argv[1] if len(sys.argv) > 1 else "meeting.wav"
if not Path(file).exists():
    sys.exit(f"Can't find {file}. Usage: python who_spoke.py conversation.mp3")
audio = decode_audio(file)                                  # 16 kHz numbers, used by both models

# 1. WHO: which speaker talks at which moment (downloads ~30 MB once, then runs offline)
try:
    diarizer = Pipeline.from_pretrained("pyannote/speaker-diarization-community-1", token=os.environ.get("HF_TOKEN"))
except Exception as error:
    sys.exit(f"Couldn't load pyannote: {error}\n"
             "Did you accept the model's terms on huggingface.co and set HF_TOKEN? (see the README)")
if torch.cuda.is_available():
    diarizer.to(torch.device("cuda"))                       # an NVIDIA graphics card makes it much faster
print("Finding the speakers (this is the slow part)...")
result = diarizer({"waveform": torch.from_numpy(audio)[None], "sample_rate": 16000})   # [None] = add a channel axis
# "exclusive" = never two speakers at the same moment, which makes joining with the words simpler
turns = [(turn.start, turn.end, speaker) for turn, speaker in result.exclusive_speaker_diarization]
print(f"Found {len({s for _, _, s in turns})} speakers")

# 2. WHAT: the words, with start/end times
segments, _ = WhisperModel("base", device="cpu", compute_type="int8").transcribe(audio, vad_filter=True)


def speaker_of(start, end):
    """The speaker who talks the most during this piece of text."""
    overlap = {}
    for t_start, t_end, speaker in turns:
        shared = min(end, t_end) - max(start, t_start)      # how many seconds the two time ranges share
        if shared > 0:
            overlap[speaker] = overlap.get(speaker, 0) + shared
    return max(overlap, key=overlap.get) if overlap else "UNKNOWN"


# 3. JOIN: label each sentence, and merge sentences in a row from the same person
lines = []
for seg in segments:
    who = speaker_of(seg.start, seg.end)
    if lines and lines[-1][0] == who:
        lines[-1][1] += " " + seg.text.strip()
    else:
        lines.append([who, seg.text.strip(), seg.start])

with open("transcript.txt", "w", encoding="utf-8") as f:
    for who, text, start in lines:
        line = f"[{int(start // 60):02d}:{int(start % 60):02d}] {who}: {text}"
        print(line)
        f.write(line + "\n")
print("\nSaved transcript.txt")
