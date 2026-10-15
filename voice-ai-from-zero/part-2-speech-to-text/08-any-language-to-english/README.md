# 08 · Any language → English

**What you'll build:** a program that detects which of 99 languages is spoken in a recording, writes it down in that language, and translates it to English. All offline.
**Like you're 10:** the same Whisper "ears" can either write down exactly what you hear, or write it down already translated into English. You choose with one word.
**Time:** ~1 h · **Builds on:** [07 · Whisper inside the browser](../07-whisper-inside-the-browser) · **Needs:** a recording in a language other than English (or record one yourself)

## Why this matters
Travel apps, international customer support, news monitoring and subtitle work all need "what language is this, and what does it mean in English?". Whisper was trained on audio paired with English translations, so a single offline model does both jobs. That saves you a separate translation service.

## What you'll learn
- **Language identification**: Whisper listens to the first 30 seconds and guesses the language, with a confidence score.
- **`task="transcribe"` vs `task="translate"`**: transcribe writes the words in the spoken language; translate writes English.
- **Language codes**: short names like `en`, `es`, `fr`, `hi`, `zh` (ISO 639-1).
- **Model size matters more for other languages**: Whisper heard far more English than anything else in training, so small models make many more mistakes in other languages.

## Before you start
Same install as the rest of Part 2 (skip if done):
```bash
pip install openai-whisper faster-whisper "av<19" sounddevice soundfile numpy
```
- `faster-whisper` (with `"av<19"` to read audio files) does both the transcription and the translation.

No API key needed. This project uses the `small` model (~480 MB, downloaded once into the Hugging Face cache).

You need a short clip (10–60 s) in another language: record yourself (project 01) in any language you know, ask a friend, or download a short news clip.

## Run it
1. From the course folder:
   ```bash
   cd part-2-speech-to-text/08-any-language-to-english
   ```
2. Run it with your clip:
   ```bash
   python translate_speech.py spanish_clip.mp3
   ```
   With no file name, it uses project 01's `my_voice.wav`.

### What you should see
For a Spanish clip:
```
🌍 Detected language: es (97% sure)

📝 What they said:
   Hola, me llamo Ana. Mañana vamos a la playa con mis amigos.

🇬🇧 In English:
   Hello, my name is Ana. Tomorrow we're going to the beach with my friends.
```
For an English recording:
```
🌍 Detected language: en (99% sure)

📝 What they said:
   The quick brown fox jumps over the lazy dog. Machine learning is fun.

(It's already English, so there is nothing to translate.)
```
Look at the confidence. Above 90% is a clear answer; below 50% means the clip is too short, too noisy, or mixes languages. When we tried the same Spanish clip with a `base`-size model it wrote "me jamuana, manyanabamos": that's why this project uses `small`.

## How it works
Open `translate_speech.py`.

1. **Choose the file** from the command line (or project 01's recording) and stop with a clear message if it doesn't exist.
2. **Load `small`.** `WhisperModel("small", device="cpu", compute_type="int8")`. For non-English speech, `small` is the smallest size that works well.
3. **First pass: transcribe.** `model.transcribe(path, task="transcribe")` returns two things:
   - `info`, ready immediately, because Whisper detects the language *before* writing anything: `info.language` (a code like `es`) and `info.language_probability` (0 to 1). `:.0%` prints 0.97 as `97%`.
   - `original`, the segments, filled in when the `" ".join(...)` line reads them.
4. **Second pass: translate, only if needed.** If the language isn't `en`, `model.transcribe(path, task="translate")` runs Whisper again, but now the decoder is told to write English. Same model, same audio, one different word.
5. **Already English?** The `else:` branch says so instead of translating English into English.

```
clip.mp3 ──▶ Whisper: which language? ──▶ "es" (97%)
                │
                ├── task="transcribe" ──▶ "Hola, me llamo Ana..."
                └── task="translate"  ──▶ "Hello, my name is Ana..."
```

## If something goes wrong
- **Wrong language detected** (e.g. Portuguese for Spanish, or `nn` for English) → the clip is too short or noisy. Use 10+ seconds of clear speech, or tell Whisper the language: `model.transcribe(path, task="translate", language="es")`.
- **The "translation" is still in the original language** → this happens sometimes with small models. Try `"medium"` (1.5 GB). Note: `large-v3-turbo` and `turbo` were **not** trained to translate; use `medium` or `large-v3` for translation.
- **`Can't find ...my_voice.wav`** → pass a file name, or record one with project 01.
- **Very slow** → it runs Whisper twice (transcribe, then translate). For long files, keep only the translate pass.
- **Odd characters on Windows** (`�`) → your terminal font lacks the script (e.g. Hindi, Chinese). Use Windows Terminal, or save the text to a file with `encoding="utf-8"`.

## Try this
1. **Easy:** try a mixed-language clip ("Hinglish", "Spanglish"). What language does it detect, and how does the transcription handle the mix?
   <details><summary>Hint</summary>Whisper picks one language for the whole 30-second window, based on whichever it hears most. Mixed speech often gets partly translated or "normalised" into one language. That's a known limit of Whisper.</details>
2. **Medium:** print the detected language's full name instead of the code.
   <details><summary>Solution</summary>

   ```python
   NAMES = {"en": "English", "es": "Spanish", "fr": "French", "de": "German", "hi": "Hindi",
            "pt": "Portuguese", "it": "Italian", "zh": "Chinese", "ja": "Japanese", "ar": "Arabic"}
   print("Language:", NAMES.get(info.language, info.language))
   ```
   `.get(key, default)` returns the code itself when the name isn't in the dictionary.
   </details>
3. **Harder:** combine this with project 06 to make **English subtitles** for a foreign-language video.
   <details><summary>Hint</summary>Copy <code>srt_time</code> and <code>to_srt</code> from <code>make_subtitles.py</code> (or <code>import</code> them by putting both files in one folder). Then <code>segments, info = model.transcribe(video, task="translate", vad_filter=True)</code>, and write <code>to_srt(list(segments))</code> to a <code>.srt</code> file. The timings stay correct because Whisper translates segment by segment.</details>

## Check yourself
1. How does Whisper know the language before it writes any words?
2. What single change turns a transcription into an English translation?
3. Why does this project use `small` instead of `base`?
4. Can Whisper translate English into Spanish?

<details><summary>Answers</summary>

1. It listens to the start of the audio (up to 30 s) and predicts a language token first, with a probability.
2. `task="translate"` instead of `task="transcribe"`.
3. Small models make many more mistakes in languages other than English, because they saw much less training audio in those languages.
4. No. Whisper's translate task only goes from any language **into English**. For other directions you'd add a text translation model (or an LLM, Part 4) after transcribing.
</details>

## Learn more (optional)
- Whisper's language list and accuracy per language: https://github.com/openai/whisper#available-models-and-languages
- The Whisper paper ("Robust Speech Recognition via Large-Scale Weak Supervision"): https://arxiv.org/abs/2212.04356

## Next
→ [Part 3 · 09 · Your computer speaks](../../part-3-text-to-speech/09-your-computer-speaks)
