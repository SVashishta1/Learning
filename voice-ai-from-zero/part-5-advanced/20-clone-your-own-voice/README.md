# 20 · Clone your own voice

**What it does:** records 10 seconds of **your** voice, then speaks any text you type in a voice that sounds like you. It uses **F5-TTS**, an open-source "zero-shot" voice cloning model: it copies a voice from one short sample, with no training.

## ⚠️ Rules first
- Clone **only your own voice**, or someone who has given you clear permission. Cloning someone without consent can be illegal and is used for scams.
- Never use a cloned voice to trick people (fake calls, fake messages).
- The script makes you read a consent sentence as the sample, a habit real products also follow.
- F5-TTS's code is MIT, but the **trained model is for non-commercial use only** (CC-BY-NC). Fine for learning.

## Setup
```bash
pip install f5-tts
```
This also installs PyTorch (~2 GB). An NVIDIA GPU makes it ~20× faster; on a CPU, expect around a minute per sentence.

## Run it
```bash
cd part-5-advanced/20-clone-your-own-voice
python clone_voice.py "Good morning! Today I learned how voice cloning works."
```
The first run records your sample (`my_reference.wav`) and downloads the model.

## Tips for a better clone
- Quiet room, normal speaking voice, mouth ~20 cm from the microphone.
- The sample's **text must match exactly** what you said (that's why we use a fixed sentence).
- Try the web demo with more options: `f5-tts_infer-gradio`, then open the link it prints.

## Try this
1. Combine with project 15: let the local AI answer in *your* voice.
2. Record your sample in a different mood (excited, whispering). The clone copies the style too.
