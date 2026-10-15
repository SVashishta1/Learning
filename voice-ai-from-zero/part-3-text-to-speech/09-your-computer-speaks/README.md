# 09 · Your computer speaks

**What you'll build:** a program that reads any text aloud with the voices already built into your operating system, lists your English voices, and saves the speech as `computer_voice.wav`.
**Like you're 10:** your computer has always been able to talk; it just never had a reason to. Three lines of Python give it one.
**Time:** ~45 min · **Builds on:** [08 · Any language → English](../../part-2-speech-to-text/08-any-language-to-english) · **Needs:** speakers or headphones (Linux: `espeak-ng`)

## Why this matters
Text-to-speech (**TTS**) is the "mouth" of every voice assistant, and it's also an accessibility tool: screen readers for blind users use exactly these system voices. System voices are instant, offline and use almost no memory, so they're still used in small devices, alerts and quick prototypes, even though they sound robotic next to the neural voices in projects 10–12.

## What you'll learn
- **TTS (text-to-speech)**: turning written text into audio.
- **Speech engine**: the program in your OS that does it: SAPI5 on Windows, NSSpeechSynthesizer/AVSpeech on Mac, eSpeak on Linux.
- **`pyttsx3`**: one Python library that talks to all three engines with the same code.
- **Rate**: speaking speed in words per minute.
- **Queue + `runAndWait()`**: you first tell the engine what to do (`say`, `save_to_file`), then it does it all.

## Before you start
Activate your venv and install the Part 3 packages:
```bash
pip install pyttsx3 piper-tts kokoro-onnx soundfile sounddevice numpy
```
- `pyttsx3`: system voices (this project).
- `piper-tts`: fast neural voices (project 10).
- `kokoro-onnx`: very natural neural voices (project 11).
- `soundfile`, `sounddevice`, `numpy`: save, play and handle audio, as in Part 1.

**Linux only:** install the speech engine: `sudo apt install espeak-ng`.

No API key needed, nothing to download.

## Run it
1. From the course folder:
   ```bash
   cd part-3-text-to-speech/09-your-computer-speaks
   ```
2. Make it say something (put your text in quotes):
   ```bash
   python speak.py "I am learning voice AI."
   ```
3. Listen, then open `computer_voice.wav` to hear the saved copy.

### What you should see
On Linux (eSpeak), we got:
```
Your computer has 131 voices. The English ones:
  22: English (Caribbean)
  23: English (Great Britain)
  24: English (Scotland)
  ...
  28: English (America)
  29: English (America, New York City)
Using voice 22: English (Caribbean)
Audio saved to computer_voice.wav
🔊 Done (also saved computer_voice.wav)
```
On Windows it looks like this:
```
Your computer has 2 voices. The English ones:
  0: Microsoft David Desktop - English (United States)
  1: Microsoft Zira Desktop - English (United States)
Using voice 0: Microsoft David Desktop - English (United States)
🔊 Done (also saved computer_voice.wav)
```
You hear the sentence in a clear but robotic voice. The numbers on the left are what you put in `VOICE_NUMBER` to choose a voice.

## How it works
Open `speak.py`.

1. **The text.** `" ".join(sys.argv[1:])` joins all the words you typed after the file name. If you typed none, the `or` picks a default sentence.
2. **Start the engine.** `pyttsx3.init()` finds your OS's speech engine and connects to it.
3. **List the voices.** `engine.getProperty("voices")` returns a list of voice objects, each with a `name`, an `id` and `languages` (codes like `en-US`).
4. **Find the English ones.** The `english = [...]` line is a **list comprehension**: "for every voice, keep its number `i` if any of its language codes starts with `en`". We print up to 10 of them.
5. **Pick a voice.** If `VOICE_NUMBER` is `None`, we use the first English voice; otherwise your number. `engine.setProperty("voice", voices[VOICE_NUMBER].id)` selects it.
6. **Set the speed.** `engine.setProperty("rate", 170)`: 170 words per minute is a calm reading pace.
7. **Queue and run.** `engine.say(text)` and `engine.save_to_file(text, "computer_voice.wav")` only add jobs to a queue. `engine.runAndWait()` does both jobs and waits until they're finished.

```
"I am learning voice AI." ──▶ pyttsx3 ──▶ your OS's speech engine ──┬──▶ speakers
                                                                    └──▶ computer_voice.wav
```
System voices are made with rules and recorded sound pieces, not a big neural network. That's why they're instant and tiny but sound flat.

## If something goes wrong
- **Linux: `RuntimeError: This means you probably do not have eSpeak or eSpeak-ng installed!`** → `sudo apt install espeak-ng`, then try again.
- **The program finishes but you hear nothing** → check volume and the default output device. On Linux you may also need `sudo apt install alsa-utils` for playback. Open `computer_voice.wav` to check the voice works.
- **It speaks in a foreign accent or another language** → pick an English voice number from the list and set `VOICE_NUMBER` to it.
- **Mac: an error that mentions `objc` or `pyobjc` when the engine starts** → run `pip install -U pyobjc`, then try again.
- **`computer_voice.wav` is missing or empty** (some Windows/Mac versions) → comment out the `engine.say(text)` line and run again; a few engine versions can't speak and save in the same run.

## Try this
1. **Easy:** try three different voices from your list.
   <details><summary>Hint</summary>Change <code>VOICE_NUMBER = None</code> to a number shown in the list, e.g. <code>VOICE_NUMBER = 1</code>. To see non-English voices too, change <code>english[:10]</code> to <code>range(len(voices))</code>.</details>
2. **Medium:** set the rate to 100 and to 300. Then make the volume half as loud.
   <details><summary>Hint</summary><code>engine.setProperty("rate", 100)</code>, and <code>engine.setProperty("volume", 0.5)</code> (1.0 = full volume). Put them before <code>engine.say(...)</code>.</details>
3. **Harder:** make it read a whole text file aloud, one line at a time, printing each line as it speaks.
   <details><summary>Solution</summary>

   Replace everything from `engine.say(text)` to the end with:
   ```python
   for line in open("story.txt", encoding="utf-8"):
       if line.strip():
           print("🔊", line.strip())
           engine.say(line.strip())
           engine.runAndWait()          # speak this line before moving to the next
   ```
   Create `story.txt` in this folder first with a few lines of text.
   </details>

## Check yourself
1. Why doesn't `engine.say(text)` speak immediately?
2. What does `pyttsx3` do that you would otherwise need three different pieces of code for?
3. Why do system voices sound more robotic than the voices in the next project?
4. What would `python speak.py` (with no text) say?

<details><summary>Answers</summary>

1. It only adds the job to a queue. `runAndWait()` actually runs the queue.
2. It talks to Windows' SAPI5, Mac's speech synthesizer and Linux's eSpeak through one API.
3. They're built from rules and small recorded sound pieces, not a neural network trained on hours of real human speech.
4. The default sentence: "Hello! I am your computer. I can talk without the internet."
</details>

## Learn more (optional)
- pyttsx3 docs: https://pyttsx3.readthedocs.io
- Search YouTube for "how text to speech works" (from rule-based to neural).

## Next
→ [10 · Natural voices with Piper](../10-natural-voices-with-piper)
