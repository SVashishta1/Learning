# 18 · Who spoke when

**What it does:** turns a conversation recording into a transcript that says **who** said each line:
```
[00:00] SPEAKER_00: Thanks for joining. Shall we start with the budget?
[00:04] SPEAKER_01: Sure. We're about ten percent over this month.
```
This is called **speaker diarization**. It uses **pyannote**, an open-source model that runs on your computer.

## One-time setup (10 minutes)
pyannote's models are free, but the authors ask you to accept their terms and log in to download them:
1. Make a free account at https://huggingface.co
2. Open https://huggingface.co/pyannote/speaker-diarization-community-1 and click **Agree / Access repository**.
3. Create a token at https://huggingface.co/settings/tokens (type "Read"), and copy it.
4. Install and set the token:
   ```bash
   pip install pyannote.audio
   # Mac/Linux:   export HF_TOKEN=hf_xxx
   # Windows:     set HF_TOKEN=hf_xxx
   ```
The token is only used for the first download. After that, everything runs offline.

## Run it
Record a conversation with a friend (or download a podcast clip), then:
```bash
cd part-5-advanced/18-who-spoke-when
python who_spoke.py conversation.mp3
```
It's slow on a CPU (roughly 1 minute per 1–2 minutes of audio). Start with a 2-minute clip.

## How the join works
pyannote gives *time ranges* per speaker; Whisper gives *sentences with times*. `speaker_of()` picks, for each sentence, the speaker who overlaps it the most.

## Try this
1. If you know there are exactly 2 people: `diarizer(..., num_speakers=2)`. It gets more accurate.
2. Replace `SPEAKER_00` with real names: a small dictionary `{"SPEAKER_00": "Ana"}`.
