# Part 1 · Sound basics

To a computer, sound is just **a long list of numbers**: how far the microphone was pushed, measured thousands of times per second. Every voice AI starts by getting those numbers, so that's where we start.

| # | Project | What you'll have | Time |
|---|---------|------------------|------|
| 01 | [Record and play your voice](01-record-and-play-your-voice) | a 5-second voice recorder in Python, and `my_voice.wav` for later projects | 45 min |
| 02 | [See your voice](02-see-your-voice) | pictures of your voice: the wave and its "fingerprint" (spectrogram) | 1 h |
| 03 | [Voice recorder in the browser](03-voice-recorder-in-the-browser) | record, play back, download, and watch a live volume meter, with no install | 1 h |

**Install once** (in your activated virtual environment, see the [course setup](../README.md#setup-once)):
```bash
pip install sounddevice soundfile numpy matplotlib
```
- `sounddevice`: microphone and speakers · `soundfile`: read/write `.wav` · `numpy`: lists of numbers · `matplotlib`: charts.
- **Linux only:** `sudo apt install libportaudio2` (the audio library `sounddevice` uses).

**You'll need:** a microphone (the built-in laptop one is fine) and speakers or headphones. Nothing is downloaded and no API key is needed.

**By the end of Part 1 you can explain:** sample, sample rate (16 kHz), mono vs stereo, WAV file, waveform, spectrogram, and RMS loudness.

Start here → [01 · Record and play your voice](01-record-and-play-your-voice)
