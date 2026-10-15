# 20 · Clone your own voice

**What you'll build:** a program that records 10 seconds of **your** voice, then speaks any text you type in a voice that sounds like you. It uses **F5-TTS**, an open-source "zero-shot" voice cloning model: it copies a voice from one short sample, with no training.
**Like you're 10:** you give the model a short example of how you sound and what you said. It learns the "sound" of your voice from that one example and uses it to read new sentences.
**Time:** ~2 h (plus a big download) · **Builds on:** [19 · Real-time assistant with interruptions](../19-real-time-assistant-with-interruptions) and Kokoro from [11](../../part-3-text-to-speech/11-studio-quality-voices-with-kokoro) · **Needs:** a microphone, ~5 GB of free disk, patience on a CPU (an NVIDIA GPU makes it ~20× faster)

## ⚠️ Rules first
- Clone **only your own voice**, or someone who has given you clear permission. Cloning someone without consent can be illegal and is used for scams.
- Never use a cloned voice to trick people (fake calls, fake messages, pretending to be someone).
- The script makes you read a consent sentence as the sample, a habit responsible products also follow.
- F5-TTS's code is MIT-licensed, but the **trained model is for non-commercial use only** (CC-BY-NC). Fine for learning; not for a product you sell.

## Why this matters
Voice cloning powers audiobook narration in an author's own voice, dubbing films into other languages with the original actor's voice, and giving people who are losing their voice (for example from ALS) a synthetic copy of it. It's also behind phone scams. Understanding how easy it has become (10 seconds of audio!) helps you build responsibly and spot misuse.

## What you'll learn
- **Zero-shot voice cloning**: copying a voice the model never trained on, from one short example.
- **Reference audio + reference text**: the sample and the exact words in it; the model lines them up to learn how *you* pronounce sounds.
- **Flow matching / diffusion**: the model starts from noise and refines it, step by step (`nfe_step=32` steps by default), into speech. More steps = better quality, slower.
- **Consent**: a simple technical habit (recording a consent sentence) that supports an ethical rule.

## Before you start
1. Install F5-TTS (this also installs PyTorch, ~2 GB, and many other packages):
   ```bash
   pip install f5-tts sounddevice soundfile
   ```
   - `f5-tts`: the voice-cloning model and its code.
   - `sounddevice` + `soundfile`: record your sample and play the result.

   Tip: if pip reports version conflicts with your other packages, make a fresh venv just for this project.
2. ffmpeg must be installed (course setup); F5-TTS uses it to read and trim your sample.
3. No API key needed. The first run downloads the model (~1.3 GB) and a small vocoder from Hugging Face into `~/.cache/huggingface`.
4. Find a quiet room. Sit about 20 cm from the microphone.

## Run it
1. From the course folder:
   ```bash
   cd part-5-advanced/20-clone-your-own-voice
   python clone_voice.py "Good morning! Today I learned how voice cloning works."
   ```
2. Press Enter and read the consent sentence aloud, calmly, in your normal voice. Recording stops by itself after 10 seconds.
3. Wait: the first run downloads the model, then generates the speech (about a minute per sentence on a CPU, a few seconds on a GPU).
4. Listen. Your sample is saved as `my_reference.wav`, so next time it skips straight to step 3. Delete that file to record a new sample.

### What you should see
```
Press Enter, then read this out loud, calmly and clearly (you have 10 seconds):

   I am recording my own voice, and I agree to clone it for my personal learning project.

🔴 Recording...
Saved my_reference.wav. (Delete it to record again.)
Download Vocos from huggingface charactr/vocos-mel-24khz
Converting audio...
Using custom reference text...

ref_text   I am recording my own voice, and I agree to clone it for my personal learning project.
gen_text 0 Good morning! Today I learned how voice cloning works.

Generating audio in 1 batches...
100%|██████████████████████████████████| 1/1 [00:52<00:00, 52.31s/it]
🔊 cloned.wav
```
Then `cloned.wav` plays: your new sentence, in a voice that should sound recognisably like yours, including your accent. (We couldn't download the 1.3 GB model in our test environment, so we checked the recording and playback steps with a stand-in for F5-TTS; the lines above show what F5-TTS itself prints.)

## How it works
Open `clone_voice.py`.

1. **Record the sample (once).** If `my_reference.wav` doesn't exist: show the `CONSENT` sentence, record `10 * 24000` samples at 24 kHz with `sd.rec(...)` (24 kHz is the rate F5-TTS works at), and check the loudest sample: under 0.02 means the microphone heard nothing, so it stops instead of cloning silence. Then save it.
2. **Import F5-TTS late.** `from f5_tts.api import F5TTS` is placed *after* recording because importing it takes many seconds; this way you can record straight away.
3. **Load the model.** `F5TTS()` downloads (first time) and loads the default model, `F5TTS_v1_Base`, onto your GPU if you have one (NVIDIA CUDA or Apple Silicon), otherwise the CPU.
4. **Clone.** `f5.infer(ref_file=SAMPLE, ref_text=CONSENT, gen_text=text, file_wave="cloned.wav", remove_silence=True)`:
   - trims silence from your sample and keeps at most 12 s;
   - joins *reference text + new text* and treats the job as "continue this recording": the reference audio is given, and the model fills in the audio for the new text in the same voice;
   - it does that by starting from random noise and improving it in 32 small steps (**flow matching**);
   - a **vocoder** (Vocos) turns the result (a spectrogram, like project 02's picture) into a waveform;
   - `remove_silence=True` trims long pauses, and the file is saved.
5. **Play** `cloned.wav`.

```
my_reference.wav + "I am recording my own voice..." ──┐
                                                       ├──▶ F5-TTS (noise → 32 steps → spectrogram) ──▶ Vocos ──▶ cloned.wav
"Good morning! Today I learned..." ───────────────────┘
```
That's why `ref_text` must match the sample exactly: if the words are wrong, the model lines up the wrong sounds with the wrong letters, and the clone mumbles.

## If something goes wrong
- **`That recording is silent`** → check microphone permission and the input device (project 01), then run again.
- **The clone sounds mumbled, robotic or not like you** → re-record (delete `my_reference.wav`) in a quiet room, reading the sentence exactly as written, without long pauses. Echoey rooms and background noise get copied too.
- **`RuntimeError: Could not load libtorchcodec`** (or an error mentioning `torchcodec` / FFmpeg libraries) → PyTorch's audio reader needs FFmpeg's shared libraries. Mac: `brew install ffmpeg`. Linux: `sudo apt install ffmpeg`. Windows: install the shared build (`winget install Gyan.FFmpeg.Shared`) and reopen the terminal.
- **Very slow (several minutes per sentence)** → normal on a CPU. Use short sentences, or a computer with an NVIDIA GPU. On a GPU, PyTorch must be the CUDA version: see https://pytorch.org/get-started/locally/.
- **pip errors while installing `f5-tts`** → use Python 3.10–3.12 in a fresh venv: `python -m venv .venv-f5`, activate it, then the pip line again.

## Try this
1. **Easy:** make it read three different sentences. Notice it reuses your saved sample each time.
   <details><summary>Hint</summary><code>python clone_voice.py "Hi, it's me. I'll be home late tonight."</code> and so on. Each run overwrites <code>cloned.wav</code>; rename it if you want to keep one. (A note on the example sentence: that's exactly the kind of message a scammer would fake. Now you know why you should verify surprising voice messages.)</details>
2. **Medium:** record your sample in a different mood (excited, or whispering) and compare. The clone copies the style too.
   <details><summary>Hint</summary>Rename <code>my_reference.wav</code> to <code>calm.wav</code>, run again to record an excited sample, and listen to both results. To switch between them, set <code>SAMPLE = "calm.wav"</code>. You can also try <code>speed=0.9</code> in <code>f5.infer(...)</code> for slower speech.</details>
3. **Harder:** combine with project 15: let the local AI answer in *your* voice.
   <details><summary>Hint</summary>In project 15's <code>talk.py</code>, load <code>f5 = F5TTS()</code> once at the top, and replace the body of <code>speak(text)</code> with <code>wav, rate, _ = f5.infer(ref_file="my_reference.wav", ref_text=CONSENT, gen_text=text)</code> then <code>sd.play(wav, rate); sd.wait()</code> (copy <code>my_reference.wav</code> and the <code>CONSENT</code> sentence over). It will be slow on a CPU: that's why real-time assistants use fast voices like Kokoro or Piper.</details>

## Check yourself
1. What does "zero-shot" mean in "zero-shot voice cloning"?
2. Why must `ref_text` match exactly what you said in the sample?
3. Why does the script record a consent sentence rather than any random text?
4. Why isn't F5-TTS a good choice for project 19's real-time assistant on a laptop?

<details><summary>Answers</summary>

1. The model was never trained on your voice; it copies it from one example at the moment of use.
2. The model aligns the text with the sounds in the sample to learn how you pronounce things. Wrong text = wrong alignment = poor quality.
3. So every clone starts with a recorded, spoken agreement from the voice's owner, which makes it clear the voice was used with consent.
4. It's slow on a CPU (often around a minute per sentence), and a real-time assistant needs speech in about a second.
</details>

## Learn more (optional)
- F5-TTS on GitHub (models, licence, the web demo `f5-tts_infer-gradio`): https://github.com/SWivid/F5-TTS
- The F5-TTS paper: https://arxiv.org/abs/2410.06885
- Search YouTube for "voice cloning scams how to protect your family" (the other side of this technology).

## Next
→ [21 · Measure accuracy](../21-measure-accuracy)
