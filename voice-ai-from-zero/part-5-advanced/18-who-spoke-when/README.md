# 18 · Who spoke when

**What you'll build:** a program that turns a conversation recording into a transcript that says **who** said each line, and saves it as `transcript.txt`:
```
[00:00] SPEAKER_00: Thanks for joining. Shall we start with the budget?
[00:03] SPEAKER_01: Sure, we are about 10% over this month.
```
This is called **speaker diarization**. It uses **pyannote**, an open-source model that runs on your computer, together with Whisper.
**Like you're 10:** one helper only listens to *voices* and says "person A talked from 0 to 3 seconds, person B from 3 to 6". Another helper writes down the *words*. We match the two lists by time.
**Time:** ~2 h (plus a one-time 10-minute sign-up) · **Builds on:** [17 · Hands-free with voice detection](../17-hands-free-with-voice-detection) · **Needs:** a free Hugging Face account and token, ~3 GB of disk for PyTorch and pyannote, a recording with 2+ people

## Why this matters
Meeting tools (Otter, Zoom's AI notes, Teams recaps), podcast editors, call-centre analytics and court transcription all need "who said what". Without it, a meeting transcript is a wall of text. pyannote is the open-source model most of these pipelines are built on.

## What you'll learn
- **Speaker diarization**: splitting audio by speaker, without knowing who they are (labels like `SPEAKER_00`, `SPEAKER_01`).
- **Speaker embedding**: a list of numbers that describes a voice; similar voices get similar numbers, which is how pyannote groups turns by person.
- **Gated model**: free to download, but you must accept the authors' terms and use a **token** (a password for programs).
- **Joining by time overlap**: matching two lists of time ranges (speaker turns and sentences).

## Before you start
1. **Packages.** Part 5's line, plus pyannote (big: it brings PyTorch, torchaudio and more):
   ```bash
   pip install faster-whisper "av<19" sounddevice numpy silero-vad jiwer scipy
   pip install pyannote.audio
   ```
   - `pyannote.audio`: the diarization model (version 4 or newer).
   - `faster-whisper`: the words, and `decode_audio` to read the file for both models.
2. **A Hugging Face token** (once, ~10 minutes). The model is free, but its authors ask you to accept their terms:
   1. Make a free account at https://huggingface.co
   2. Open https://huggingface.co/pyannote/speaker-diarization-community-1 and accept the conditions (**Agree and access repository**).
   3. Create a token at https://huggingface.co/settings/tokens (type **Read**) and copy it (it starts with `hf_`).
   4. Put it in an environment variable in the terminal you'll use:
      - Mac/Linux: `export HF_TOKEN=hf_xxx`
      - Windows (Command Prompt): `set HF_TOKEN=hf_xxx` · Windows (PowerShell): `$env:HF_TOKEN="hf_xxx"`

   The token is only needed for the first download (~30 MB into `~/.cache/huggingface`). Never share it or put it in your code.
3. **A recording** of 2–4 people talking: record yourself and a friend for 2 minutes (project 01 with `SECONDS = 120`, or your phone), or download a podcast clip. Start short: diarization is slow on a CPU.

## Run it
1. From the course folder:
   ```bash
   cd part-5-advanced/18-who-spoke-when
   python who_spoke.py conversation.mp3
   ```
   (Use your file's real name or full path.)
2. Read the result on screen or in `transcript.txt` (in this folder).

### What you should see
We used a 12-second, two-person test conversation:
```
Finding the speakers (this is the slow part)...
Found 2 speakers
[00:00] SPEAKER_00: Thanks for joining. Shall we start with the budget?
[00:03] SPEAKER_01: Sure, we are about 10% over this month.
[00:06] SPEAKER_00: Okay, what caused that?
[00:08] SPEAKER_01: Mostly the new laptops, they arrived early.

Saved transcript.txt
```
On a laptop CPU, expect roughly 1 minute of processing per 1–2 minutes of audio, plus a minute for the first download. You may also see a warning that starts with `torchcodec is not installed correctly`: that's fine, because this script hands pyannote the audio already decoded (see step 2 below).

## How it works
Open `who_spoke.py`.

1. **Read the audio once.** `decode_audio(file)` gives 16 kHz mono numbers, used by both models.
2. **WHO.** `Pipeline.from_pretrained("pyannote/speaker-diarization-community-1", token=...)` downloads (first time) and loads the diarization pipeline. If that fails (no token, terms not accepted, no internet), the `except` prints a clear hint. `diarizer({...})` runs it on a dictionary with the audio as a PyTorch tensor and its sample rate; `[None]` adds a "channel" dimension, because pyannote expects the shape (channels, samples). Passing audio this way avoids pyannote's own file reader (torchcodec), which needs extra FFmpeg libraries on some computers.
   Inside, pyannote: finds speech, cuts it into short pieces, computes a **speaker embedding** for each piece, and **clusters** them: pieces with similar voices get the same label.
3. **Turns.** We use `result.exclusive_speaker_diarization`, a version with no overlapping speech (only one speaker at any moment), which is simpler to join with words. Each turn becomes `(start, end, speaker)`.
4. **WHAT.** Whisper transcribes the same audio into segments with start and end times (project 04).
5. **JOIN with `speaker_of(start, end)`.** For each Whisper segment, it adds up how many seconds each speaker overlaps it: `min(end, t_end) - max(start, t_start)` is the length of the shared part of two time ranges (negative if they don't touch). The speaker with the most shared time wins.
6. **Merge and save.** Consecutive segments from the same speaker are joined into one line. `int(start // 60)` and `int(start % 60)` turn seconds into `mm:ss`.

```
                 ┌──▶ pyannote: SPEAKER_00 0.5–3.1 s, SPEAKER_01 3.7–6.1 s, ...
conversation ────┤                                                            ├──▶ speaker_of() ──▶ transcript.txt
                 └──▶ Whisper:  "Thanks for joining..." 0.5–3.1 s, ...        ┘
```

## If something goes wrong
- **`Couldn't load pyannote: ... 401 ... gated repo` (or 403)** → you didn't accept the terms on the model page, or `HF_TOKEN` isn't set *in this terminal*. Redo setup step 2, then run `echo $HF_TOKEN` (Mac/Linux) or `echo %HF_TOKEN%` (Windows) to check.
- **`ModuleNotFoundError: No module named 'pyannote'`** → `pip install pyannote.audio` in your activated venv.
- **Pip fails with version conflicts on torch** → install it in a fresh venv: `pip install pyannote.audio faster-whisper "av<19"`.
- **It finds too many speakers** (the same person split into two) → tell it the number: see "Try this" 1. Background noise and laughter make this worse.
- **Very slow** → use a 2-minute clip first. A GPU (NVIDIA + CUDA PyTorch) makes it about 10× faster; the script uses it automatically.

## Try this
1. **Easy:** if you know exactly how many people are talking, tell pyannote. It gets more accurate.
   <details><summary>Hint</summary>Change the diarizer call to <code>diarizer({...}, num_speakers=2)</code>. If you only know a range, use <code>min_speakers=2, max_speakers=4</code>.</details>
2. **Medium:** replace `SPEAKER_00` with real names.
   <details><summary>Solution</summary>

   Add near the top: `NAMES = {"SPEAKER_00": "Ana", "SPEAKER_01": "Ben"}`, then in the final loop:
   ```python
   line = f"[{int(start // 60):02d}:{int(start % 60):02d}] {NAMES.get(who, who)}: {text}"
   ```
   Run once first to see who is `SPEAKER_00` (usually whoever speaks first). `.get(who, who)` keeps the label if the name isn't in the dictionary.
   </details>
3. **Harder:** print how long each person spoke in total, to see who dominated the conversation.
   <details><summary>Solution</summary>

   Add at the end:
   ```python
   talk_time = {}
   for start, end, speaker in turns:
       talk_time[speaker] = talk_time.get(speaker, 0) + (end - start)
   for speaker, seconds in sorted(talk_time.items(), key=lambda item: -item[1]):
       print(f"{speaker}: {seconds:.0f} s")
   ```
   `sorted(..., key=lambda item: -item[1])` sorts by seconds, biggest first.
   </details>

## Check yourself
1. Diarization tells you "who spoke when". What does it *not* tell you?
2. Why does the script use `exclusive_speaker_diarization` rather than `speaker_diarization`?
3. A Whisper segment runs from 10 s to 14 s. SPEAKER_00 talks 9–11 s and SPEAKER_01 talks 11–15 s. Who gets the segment, and why?
4. Why does the program need a token at all, if the model is free?

<details><summary>Answers</summary>

1. Their names, or what they said. It only gives anonymous labels and time ranges; the words come from Whisper and the names from you.
2. The exclusive version never has two speakers at the same moment, so each moment belongs to one person, which makes assigning sentences simpler.
3. SPEAKER_01: it overlaps for 3 seconds (11–14), SPEAKER_00 only for 1 second (10–11).
4. The model is "gated": its authors ask users to accept their terms. Hugging Face uses your token to check you did.
</details>

## Learn more (optional)
- pyannote.audio on GitHub: https://github.com/pyannote/pyannote-audio
- The community-1 model card: https://huggingface.co/pyannote/speaker-diarization-community-1
- Search YouTube for "speaker diarization explained".

## Next
→ [19 · Real-time assistant with interruptions](../19-real-time-assistant-with-interruptions)
