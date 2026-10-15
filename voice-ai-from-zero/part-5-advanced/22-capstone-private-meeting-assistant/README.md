# 22 · Capstone: private meeting assistant

**What you'll build:** the kind of tool companies pay for (Otter, Fireflies, Zoom's AI notes), but **100% private**: nothing leaves your computer.
1. Upload a meeting recording (audio or video) or record one in the browser.
2. Get a **timestamped transcript**, a **summary**, **decisions** and **action items** (who / what / when).
3. **Ask questions** about it ("why are we over budget?") and get answers with the time it was said.
4. **Download** everything as a Markdown file. Every meeting is saved in `meetings.db` and listed in the sidebar.

**Like you're 10:** Whisper writes down the whole meeting, then the local AI reads those notes and fills in a form: "what was decided, who has to do what, by when".
**Time:** ~1 week (build, test with real meetings, then extend) · **Builds on:** everything, especially [13](../../part-4-voice-apps/13-voice-notes-app), [15](../../part-4-voice-apps/15-talk-to-a-local-ai) and [21](../21-measure-accuracy) · **Needs:** Ollama with `llama3.2:3b`, ~8 GB of RAM, a meeting recording (or a friend to record one with)

## Why this matters
Meeting assistants are one of the most widely used AI products in companies, and many teams can't use cloud versions because meetings contain confidential information. A local version solves that. Building it combines the core skills of an AI engineer: speech-to-text, LLM prompting, **structured output** (getting data, not prose), handling long inputs, a database and a web UI.

## What you'll learn
- **Structured output (JSON mode)**: `"format": "json"` makes Ollama return valid JSON that your code can use directly.
- **Map-reduce summarisation**: a long meeting doesn't fit in a small model at once, so you summarise each piece ("map"), then summarise the summaries ("reduce").
- **Context window (`num_ctx`)**: how much text the model can read at once. Ollama's default is small; we raise it to 16,384 tokens (~12,000 words).
- **Grounded Q&A**: answering only from the transcript and citing `[mm:ss]` times, so answers can be checked.
- **Defensive code**: checking the LLM's JSON shape and Ollama's availability before doing slow work.

## Before you start
1. Packages: the Part 4 line (skip if done):
   ```bash
   pip install faster-whisper "av<19" kokoro-onnx fastapi uvicorn python-multipart httpx pyttsx3 sounddevice soundfile numpy
   ```
   This project uses `faster-whisper` (with `"av<19"` to read audio and video files, including the browser's `.webm`), `fastapi` + `uvicorn` + `python-multipart` (the web app and uploads) and `httpx` (talks to Ollama). SQLite is built into Python.
2. Ollama running with `ollama pull llama3.2:3b` done (see [project 15](../../part-4-voice-apps/15-talk-to-a-local-ai)).
3. No API key needed. The first upload downloads Whisper `small` (~480 MB) if you don't have it.
4. A meeting to test with: record yourself and a friend planning a trip for 3 minutes, use a recorded online meeting (with everyone's permission), or a podcast clip.

## Run it
1. From the course folder:
   ```bash
   cd part-5-advanced/22-capstone-private-meeting-assistant
   uvicorn server:app
   ```
2. Open http://localhost:8000.
3. Type a title, choose a file and click **Upload** (or click **🎙️ Record**, talk, then **⏹ Stop**).
4. Wait while it transcribes and summarises. Then read the summary, decisions and action items, ask a question, and click **⬇️ Download as Markdown**.
5. Click a meeting in the sidebar to open it again later. Stop the server with `Ctrl+C`; the meetings stay in `meetings.db`.

### What you should see
We uploaded a 12-second, two-person test meeting titled "Budget check". The page shows:
```
Budget check
⬇️ Download as Markdown
Summary
  The team reviewed this month's budget, which is about 10% over. The overspend is
  mostly because the new laptops arrived earlier than planned.
Decisions
  • (none)
Action items
  • unknown: Check the impact of the early laptop delivery on next month's budget (due: unknown)
Ask about this meeting
  [Why are we over budget?]  [Ask]
  Mostly because of the new laptops, which arrived early [00:08].
▸ Full transcript
  [00:00] Thanks for joining. Shall we start with the budget?
  [00:03] Sure, we are about 10% over this month.
  [00:06] Okay, what caused that?
  [00:08] Mostly the new laptops, they arrived early.
```
The downloaded `meeting-1.md` has the same sections in Markdown, with action items as a checklist (`- [ ] **unknown**: ...`). In the terminal:
```
INFO:     127.0.0.1:41000 - "POST /meetings HTTP/1.1" 200 OK
INFO:     127.0.0.1:41000 - "GET /meetings HTTP/1.1" 200 OK
INFO:     127.0.0.1:41000 - "POST /meetings/1/ask HTTP/1.1" 200 OK
INFO:     127.0.0.1:41000 - "GET /meetings/1/markdown HTTP/1.1" 200 OK
```
(We checked the full flow in a browser with a stand-in for Ollama; the summary text above is a typical `llama3.2:3b` answer, and yours will be worded differently.) Notice that the model says "unknown" when nobody was named: that's what the prompt asks for, instead of inventing a person.

## How it works
```
audio ──▶ faster-whisper "small" ──▶ "[02:15] We'll launch on Friday."
                                       │
            short meeting ─────────────┤
            long meeting: notes per 2,500 words, then combine ("map-reduce")
                                       ▼
                         Ollama (JSON mode) ──▶ {summary, decisions, action_items} ──▶ SQLite
question ──▶ Ollama + full transcript ──▶ answer with [mm:ss]
```

**`server.py`**
1. **Start-up**: load Whisper `small` (meetings deserve accuracy), open `meetings.db` and create the `meetings` table (id, title, created, transcript, summary). The summary column stores the whole `{summary, decisions, action_items}` result as a JSON string.
2. **`ask_llm(prompt, json_mode)`**: one helper for every LLM call. It sends a single user message with `"options": {"num_ctx": 16384}` so long transcripts fit, adds `"format": "json"` when we need data, and turns "Ollama isn't running" or "model not found" into a clear `HTTPException` the page can show.
3. **`transcribe(audio_bytes)`**: Whisper with `vad_filter=True`; each segment becomes one line starting with `[mm:ss]` (`int(s.start // 60)` minutes, `int(s.start % 60)` seconds).
4. **`summarize(transcript)`**:
   - **map**: if the transcript has more than 2,500 words, it's cut into 2,500-word pieces and the LLM writes bullet-point notes for each;
   - **reduce**: the LLM reads the notes (or the whole short transcript) and must reply with JSON in an exact shape, shown in the prompt: `{"summary": ..., "decisions": [...], "action_items": [{"who", "task", "due"}]}`. The prompt says "person or unknown" and "date or unknown" to discourage invented details;
   - **tidy up**: small models don't always follow the shape, so the code converts everything to the expected types (for example an action item that's just a string becomes `{"who": "unknown", "task": "...", "due": "unknown"}`).
5. **`POST /meetings` (`add_meeting`)**: first a quick `httpx.get` checks Ollama is running, so you don't wait 10 minutes for a transcription that then can't be summarised. Then transcribe → summarise → `INSERT` → return the full meeting.
6. **`GET /meetings`** lists all meetings (newest first) for the sidebar; **`GET /meetings/{id}`** returns one, combining the table columns with the stored JSON (`**json.loads(row[4])` spreads its keys into the dictionary).
7. **`POST /meetings/{id}/ask`**: a **grounded** prompt: "answer using only this transcript, quote the [mm:ss] time, and say so if the answer isn't there", followed by the transcript and the question.
8. **`GET /meetings/{id}/markdown`**: builds a Markdown document line by line; `response_class=PlainTextResponse` sends it as text, and the page's `download` attribute saves it as a file.

**`index.html`**
9. **Upload or record** both end in `send(blob, name)`, which disables the buttons, posts the file and title, and shows either the meeting or the error message (`data.detail`).
10. **`show(m)`** builds the meeting view. All text from the server is inserted with `textContent` (the `list()` helper builds `<li>` items safely), so a transcript can never inject HTML into the page. **Ask** posts the question and shows the answer.

### Limits worth knowing
- A 1-hour meeting takes around 10 minutes to process on a laptop CPU. A GPU, or `"base"` instead of `"small"`, is faster.
- Q&A sends the whole transcript; meetings over ~1.5 hours exceed the 16k context. The fix is RAG (`ai-from-zero` Part 5): search the transcript first, send only the matching parts.
- Small LLMs sometimes miss or invent action items. Always skim the transcript for anything important.
- Whisper doesn't know who is speaking, so action items often say "unknown". Make-it-yours idea 1 fixes that.

## If something goes wrong
- **"❌ Can't reach Ollama. Start the Ollama app and try again."** → start Ollama and check http://localhost:11434, then upload again.
- **"❌ I couldn't hear any speech in that file."** → the file has no speech, or the browser recording was silent (microphone permission). Try the file with project 04 first.
- **It seems stuck on "⏳ Transcribing..."** → long files take minutes. Watch the terminal: when it prints `POST /meetings ... 200 OK`, it's done. Try a 2-minute clip first.
- **`json.decoder.JSONDecodeError` in the terminal** → the model returned broken JSON (rare with `"format": "json"`, more likely if the answer was cut off). Try again, or use a bigger model (`ollama pull llama3.1:8b` and change `MODEL`).
- **Ollama runs out of memory with long meetings** → `num_ctx` 16,384 needs extra RAM. Lower it to `8192` (and the piece size from 2,500 to 1,200 words).

## Try this
1. **Easy:** change the summary length from "3-5 sentences" to "2 sentences", and add a `"next_meeting"` field to the JSON.
   <details><summary>Hint</summary>Edit the prompt in <code>summarize()</code>: add <code>"next_meeting": "date or unknown"</code> to the example JSON, and return <code>"next_meeting": str(data.get("next_meeting", "unknown"))</code> too. Delete <code>meetings.db</code> first only if you change the table; here you don't need to, because the JSON is stored as text. Show it in <code>index.html</code> like the summary.</details>
2. **Medium:** show how long processing took (transcribe vs summarise) under the title.
   <details><summary>Hint</summary>In <code>add_meeting</code>, time both steps with <code>time.time()</code> and add <code>"timing": f"transcribe {a:.0f}s · summarise {b:.0f}s"</code> to the dictionary returned by <code>get_meeting(...)</code> (e.g. <code>result = get_meeting(row.lastrowid); result["timing"] = ...; return result</code>). In <code>send()</code>, set <code>status.textContent = data.timing</code> when <code>res.ok</code>.</details>
3. **Harder:** measure your pipeline: record a 2-minute meeting, type the true transcript yourself, and compute Whisper's WER with project 21's method. Then check whether the action items the LLM found are correct.
   <details><summary>Hint</summary>Copy the text from the transcript box without the <code>[mm:ss]</code> parts (<code>re.sub(r"\[\d+:\d+\] ", "", text)</code>) and use <code>jiwer.wer(clean(truth), clean(guess))</code>. For the action items, count: found and correct, found but invented, missed. That's precision and recall, the next idea worth learning.</details>

### Bigger projects: make it yours (pick any)
1. **Speaker names**: add project 18's pyannote step so the transcript shows who said what, and action items get real owners.
   <details><summary>Hint</summary>In <code>transcribe()</code>, run the diarizer on the same audio (decode the bytes with <code>decode_audio(io.BytesIO(audio_bytes))</code>), build <code>turns</code>, and prefix each line with <code>speaker_of(s.start, s.end)</code> from <code>who_spoke.py</code>. The LLM then sees "SPEAKER_01: I'll send the report on Friday" and can fill in <code>who</code>.</details>
2. **Live mode**: transcribe while the meeting happens, using project 17's hands-free listener, and summarise when you stop.
   <details><summary>Hint</summary>Start from <code>hands_free.py</code>: append each 📝 sentence (with its time) to a list, and on <code>Ctrl+C</code> join them into a transcript and call <code>summarize()</code> (copy it and <code>ask_llm</code> from <code>server.py</code>).</details>
3. **Search across all meetings**: put every transcript in a vector database and ask "when did we last talk about hiring?".
   <details><summary>Hint</summary>Use Chroma from <code>ai-from-zero</code> Part 5: add each transcript line as a document with metadata <code>{"meeting_id": ..., "time": "02:15"}</code>, then query it with the question and send the best matches to <code>ask_llm</code>.</details>
4. **Email draft**: a button that writes a follow-up email with the action items.
   <details><summary>Solution</summary>

   Add a route to `server.py`:
   ```python
   @app.get("/meetings/{meeting_id}/email", response_class=PlainTextResponse)
   def email(meeting_id: int):
       m = get_meeting(meeting_id)
       return ask_llm("Write a short, friendly follow-up email for this meeting. List the action items "
                      f"with owners and due dates. No subject line.\n\n{json.dumps(m['action_items'])}\n\n"
                      f"SUMMARY: {m['summary']}")
   ```
   In `show(m)` add `<a href="/meetings/${m.id}/email" target="_blank">✉️ Draft follow-up email</a>` next to the download link.
   </details>

## Check yourself
1. Why does the summary use `"format": "json"`, while the Q&A answer doesn't?
2. What problem does map-reduce summarisation solve, and what's its downside?
3. Why does `add_meeting` check Ollama *before* transcribing?
4. How does the Q&A prompt reduce made-up answers?

<details><summary>Answers</summary>

1. The summary is data the code must read (summary, list of decisions, list of action items) and store; JSON mode guarantees parseable JSON. The Q&A answer is just text shown to a person.
2. It lets a small model handle meetings longer than its context window, by summarising pieces and then the notes. Downside: details can be lost between the steps, and it takes more LLM calls (slower).
3. Transcription can take many minutes. If Ollama isn't running, the summary would fail afterwards and that work would be wasted.
4. It tells the model to use only the transcript, to quote the `[mm:ss]` time (so you can check), and to say when the answer isn't there.
</details>

## Learn more (optional)
- Ollama structured outputs (JSON mode and JSON schemas): search "Ollama structured outputs".
- FastAPI tutorial, bigger applications: https://fastapi.tiangolo.com/tutorial/bigger-applications/
- Search YouTube for "map reduce summarization LLM".

## Next
🎉 You've finished **Voice AI from Zero**. You can now build private voice apps end to end: record, transcribe, understand, answer, speak, stream, and measure.

→ Continue with the [AI Engineer Journey](../../../ai-engineer-journey), which goes deeper into how models work and how to build AI products, or polish this capstone into a portfolio project (add speaker names and a README with a screenshot).
