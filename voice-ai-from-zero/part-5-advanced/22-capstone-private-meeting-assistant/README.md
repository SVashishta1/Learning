# 22 · Capstone: private meeting assistant

**What it does:** the kind of tool companies pay for (Otter, Fireflies...), but **100% private**: nothing leaves your computer.
1. Upload a meeting recording (audio or video) or record one in the browser.
2. Get a **timestamped transcript**, a **summary**, **decisions** and **action items** (who / what / when).
3. **Ask questions** about it ("what did Ana say about the deadline?"), with the time it was said.
4. **Download** everything as a Markdown file. All meetings are saved in `meetings.db`.

## Run it
Ollama running with `llama3.2:3b` (Part 4 README), then:
```bash
cd part-5-advanced/22-capstone-private-meeting-assistant
uvicorn server:app
```
Open http://localhost:8000. No meeting to hand? Record yourself and a friend planning a trip for 3 minutes, or use a podcast clip.

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
Three ideas from the whole course meet here: **Whisper** (Part 2), **local LLMs** (Part 4), and **structured output**: `format: "json"` makes the model return data your code can use, not just prose.

## Limits worth knowing
- A 1-hour meeting takes ~10 minutes to process on a laptop CPU. A GPU, or `"base"` instead of `"small"`, is faster.
- Q&A sends the whole transcript; meetings over ~1.5 hours exceed the 16k context. The fix is RAG (`ai-from-zero` Part 5): search the transcript first, send only matching parts.
- Small LLMs sometimes invent action items. Always skim the transcript for important things.

## Make it yours (pick any)
1. **Speaker names**: add project 18 so the transcript shows who said what, and action items get real owners.
2. **Live mode**: transcribe while the meeting happens, using project 17's hands-free listener.
3. **Search across all meetings**: put every transcript in a vector database and ask "when did we last talk about hiring?"
4. **Email draft**: a button that writes a follow-up email with the action items.
