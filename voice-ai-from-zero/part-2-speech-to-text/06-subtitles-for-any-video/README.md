# 06 · Subtitles for any video

**What you'll build:** a program that creates a `.srt` subtitle file for any video or podcast. Put it next to the video and players like **VLC** show the subtitles automatically.
**Like you're 10:** Whisper writes down what's said *and when*. A subtitle file is just a numbered list of "from this time to that time, show these words".
**Time:** ~1 h · **Builds on:** [05 · Faster Whisper + live microphone](../05-faster-whisper-live-microphone) · **Needs:** ffmpeg (course setup), a video or audio file

## Why this matters
Captions are required for accessibility on many platforms, help people watch without sound, and boost video reach. Creators, schools and companies pay for subtitle services that do exactly this. The same "text with timestamps" also powers searchable videos ("jump to where they mention pricing").

## What you'll learn
- **Timestamps**: Whisper gives each segment a `start` and `end` in seconds.
- **SRT format**: the most common subtitle file: a number, a time line `00:00:03,500 --> 00:00:05,000`, the text, and a blank line.
- **Formatting time**: turning `3.5` seconds into `00:00:03,500` with whole-number division (`divmod`).
- **Lazy generator**: faster-whisper doesn't transcribe until you read the segments; `list(segments)` makes it do the work.

## Before you start
Same install as the rest of Part 2 (skip if done):
```bash
pip install openai-whisper faster-whisper "av<19" sounddevice soundfile numpy
```
- `faster-whisper` does the transcription; `"av<19"` is the library it uses to read the sound out of video files.

No API key needed. This project uses the `small` model (~480 MB download, once) because subtitles deserve accuracy.

You need a video or audio file: a clip from your phone, a lecture, a podcast episode. Start with something 1–3 minutes long.

## Run it
1. From the course folder:
   ```bash
   cd part-2-speech-to-text/06-subtitles-for-any-video
   ```
2. Run it with your file (quotes are needed if the name has spaces; the file can be in another folder):
   ```bash
   python make_subtitles.py "my video.mp4"
   python make_subtitles.py "C:/Users/me/Videos/lecture.mp4"
   ```
3. The `.srt` file is created **next to the video**, with the same name. Open the video in VLC: the subtitles appear. (In other players, choose Subtitles → Add subtitle file.)

### What you should see
```
Language: en | length: 12 s. Transcribing...
✅ Wrote 2 subtitles to my video.srt. Open the video in VLC: subtitles appear automatically.
```
And `my video.srt` contains:
```
1
00:00:00,990 --> 00:00:05,600
The quick brown fox jumps over the lazy dog. Machine learning is fun.

2
00:00:07,710 --> 00:00:11,360
Hello, I am speaking from your own computer. No internet needed.
```
A 10-minute video takes a few minutes on a laptop CPU. The first line appears quickly; the long wait comes after "Transcribing...".

## How it works
Open `make_subtitles.py`.

1. **`srt_time(seconds)`** converts seconds to SRT time. It first turns the seconds into whole milliseconds (`3.5` → `3500`), then `divmod` splits them: `divmod(3500, 1000)` gives `(3, 500)`, meaning 3 seconds and 500 ms. It does the same for hours (3,600,000 ms) and minutes (60,000 ms). `:02d` pads with zeros: `3` → `03`.
2. **`to_srt(segments)`** builds the file text. `enumerate(segments, start=1)` numbers them from 1. Each block is: number, `start --> end`, text. `"\n".join(blocks)` puts a blank line between blocks.
3. **`if __name__ == "__main__":`** means "run this part only when the file is started directly", so other programs could `import` `srt_time` without transcribing anything.
4. **Check the input.** If you forgot the file name, or it doesn't exist, the program stops with an example of how to run it.
5. **Transcribe.** `model.transcribe(str(video), vad_filter=True)` reads the sound track straight out of the video file. It returns `segments` (a generator, not done yet) and `info` (language and duration, ready immediately).
6. **`list(segments)`** forces the real work: Whisper now goes through the whole file.
7. **Save.** `video.with_suffix(".srt")` makes the output name, and `write_text(..., encoding="utf-8")` saves it so accents and non-English letters work.

```
video.mp4 ──(sound track)──▶ faster-whisper ──▶ segments [start, end, text] ──▶ to_srt() ──▶ video.srt
```

## If something goes wrong
- **`Give me a video or audio file that exists`** → check the file name and folder. Tip: drag the file onto the terminal window to paste its full path.
- **The subtitles are out of sync by a fixed amount** → the video has a long silent intro or music. Try without `vad_filter=True`, or shift them in VLC (keys `G` and `H`).
- **VLC doesn't show them** → the `.srt` must have exactly the same name as the video and be in the same folder. Or use Subtitle → Add Subtitle File.
- **Strange characters (Ã©) in other players** → the file is UTF-8; choose UTF-8 encoding in the player's subtitle settings.
- **It's too slow** → change `"small"` to `"base"`. Expect a few more mistakes.

## Try this
1. **Easy:** open the `.srt` file in a text editor and look at the format. Change one word, save, and reopen the video in VLC.
   <details><summary>Hint</summary>Any plain text editor works (Notepad, TextEdit in plain-text mode, VS Code). This is how professional subtitlers fix Whisper's mistakes: generate first, then correct by hand.</details>
2. **Medium:** make **English** subtitles for a video in another language.
   <details><summary>Hint</summary>Add <code>task="translate"</code>: <code>model.transcribe(str(video), vad_filter=True, task="translate")</code>. Whisper then writes English text with the same timings. Project 08 explains this in detail.</details>
3. **Harder:** split subtitle lines longer than 42 characters into two lines (the TV standard), so they don't cover the whole screen.
   <details><summary>Solution</summary>

   Add `import textwrap` at the top, and in `to_srt` replace `seg.text.strip()` with:
   ```python
   "\n".join(textwrap.wrap(seg.text.strip(), 42))
   ```
   `textwrap.wrap` splits text into lines of at most 42 characters without cutting words in half. SRT allows several text lines per subtitle.
   </details>

## Check yourself
1. What does `srt_time(75.25)` return?
2. Why is `list(segments)` the slow line, not `model.transcribe(...)`?
3. Why is `if __name__ == "__main__":` useful here?
4. What are the 4 parts of each SRT block?

<details><summary>Answers</summary>

1. `00:01:15,250` (1 minute, 15 seconds, 250 milliseconds).
2. faster-whisper returns a lazy generator: it only transcribes when you read the segments, and `list()` reads them all.
3. Another script can `import` `srt_time` and `to_srt` and reuse them, without starting a transcription.
4. The number, the time line (`start --> end`), the text, and a blank line.
</details>

## Learn more (optional)
- The SRT format explained: search "SubRip srt file format".
- faster-whisper options (word timestamps, VAD settings): https://github.com/SYSTRAN/faster-whisper

## Next
→ [07 · Whisper inside the browser](../07-whisper-inside-the-browser)
