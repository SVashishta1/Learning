# Draw two pictures of a recording: the WAVE (loudness over time) and the SPECTROGRAM (which pitches, when).
# Usage: python see_voice.py ../01-record-and-play-your-voice/my_voice.wav
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import soundfile as sf

path = sys.argv[1] if len(sys.argv) > 1 else "../01-record-and-play-your-voice/my_voice.wav"
if not Path(path).exists():
    sys.exit(f"Can't find {path}. Record one first with project 01, or pass a file: python see_voice.py some.wav")
audio, rate = sf.read(path)                        # audio = the numbers, rate = how many per second
if audio.ndim > 1:
    audio = audio.mean(axis=1)                     # stereo -> mono
seconds = np.arange(len(audio)) / rate             # the time of each number, for the x-axis

fig, (top, bottom) = plt.subplots(2, 1, figsize=(10, 6))
top.plot(seconds, audio, linewidth=0.5)
top.set_title("The wave: how hard the microphone was pushed, over time")
top.set_xlabel("seconds")

# Cut the audio into small overlapping windows (512 numbers each) and measure every pitch in each window
bottom.specgram(audio, Fs=rate, NFFT=512, noverlap=384, cmap="magma")
bottom.set_title("The spectrogram: low pitches at the bottom, high at the top, bright = loud")
bottom.set_xlabel("seconds"); bottom.set_ylabel("pitch (Hz)")
plt.tight_layout()
plt.savefig("my_voice.png", dpi=110)
print(f"Saved my_voice.png  ({len(audio) / rate:.1f} s of audio at {rate} samples/second)")

# Find the quiet and loud parts: loudness in 0.1-second slices
slice_len = rate // 10                             # 0.1 s worth of numbers
loudness = [np.sqrt(np.mean(audio[i:i + slice_len] ** 2)) for i in range(0, len(audio) - slice_len + 1, slice_len)]
# RMS (root mean square) = the average size of the numbers = loudness. Each slice becomes one bar character.
print("Loudness every 0.1 s:", "".join(" ▁▂▃▄▅▆▇█"[min(8, int(l * 60))] for l in loudness))
