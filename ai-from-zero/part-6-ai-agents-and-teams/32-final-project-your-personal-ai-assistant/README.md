# 32 · Final project: your personal AI assistant 🎓

**What you'll build:** a web app run by a **team of AI agents**. A receptionist AI reads each message and hands it to the right specialist:

| Specialist | Uses | Built in |
|-----------|------|----------|
| 📚 **Librarian** | your documents (upload PDFs!) via a **vector database** | Part 5 |
| 🌍 **Researcher** | live **web search** | Part 6 |
| ✅ **Organizer** | your **to-do list** in a database | Part 1 |
| 💬 **Chatter** | friendly conversation, with **memory** | Part 4 |

**Time:** ~2 hours to run and understand, then as long as you like to make it yours · **Builds on:** everything, especially [24](../../part-5-rag-and-vector-databases/24-rag-ask-your-documents) (RAG), [28](../28-agent-with-many-tools) (agent engine) and [30](../30-ai-customer-support-team) (router + specialists) · **Needs:** an Anthropic API key and an internet connection

## Why this matters
This is a complete, small version of what AI engineers build at work: a web front end, an API, a router agent, specialist agents with their own tools, a vector database for private documents, live web search and a normal database for app data. Every piece is something you built earlier in the course, now working together. Finished and personalised, it's a portfolio project you can demo in an interview.

## What you'll learn
- **System design:** how a browser, an API, a router and several agents fit together into one product.
- **Routing with context:** the receptionist looks at the recent chat too, so "and add that to my list" goes to the right specialist.
- **Shared memory:** one conversation history is passed to whichever specialist answers, so the team feels like one assistant.
- **Showing your work:** each reply says which specialist answered and which tools it used, so users (and you) can trust and debug it.

## Before you start
- Install the Part 6 packages (once):
  ```bash
  pip install anthropic chromadb pypdf fastapi "uvicorn[standard]" python-multipart httpx tzdata
  ```
  Used here: `anthropic` (Claude), `chromadb` (vector database), `pypdf` (reads PDFs), `fastapi` + `uvicorn` (the web app), `python-multipart` (file uploads). The to-do list uses `sqlite3`, which is built into Python.
- Set your API key in the terminal you'll start the app from (full steps in the [Part 4 README](../../part-4-chatbots)):
  ```bash
  export ANTHROPIC_API_KEY=sk-ant-your-key-here        # Mac
  $env:ANTHROPIC_API_KEY="sk-ant-your-key-here"        # Windows PowerShell
  ```

## Run it
1. From the course folder (`Learning/ai-from-zero`), with your venv switched on:
   ```bash
   cd part-6-ai-agents-and-teams/32-final-project-your-personal-ai-assistant
   uvicorn app:app --reload
   ```
2. Open http://127.0.0.1:8000 and click the three example buttons at the top (📚 my docs, 🌍 web, ✅ tasks).
3. Then try your own messages:
   - `What's the meal allowance in the expense policy?` → 📚
   - `Who won the last Champions League final?` → 🌍
   - `Add 'apply to 3 AI internships' to my list` → ✅, then `show my tasks`, then `mark task 1 as done`
   - Click **⬆ Upload**, add your CV as a PDF, and ask `What are my strongest skills according to my CV?` → 📚
4. Stop the server with `Ctrl + C`. Your tasks (`tasks.db`) and documents (`chroma_data`) are saved and come back next time.

### What you should see
In the terminal:
```
INFO:     Started server process [10156]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
```
In the browser, a chat on the left and your to-do list on the right (hidden on narrow phone screens). After clicking the three buttons, the conversation looks like this (wording will differ):
```
You:          What does my study plan say I find hard?
📚 Librarian:  Your study plan (my_study_plan.md) says you find neural network maths and Docker hard.
               It suggests rewatching the 3Blue1Brown videos and redoing project 05.
               🔧 search_my_documents({"question": "things I find hard"})

You:          What is one big AI news story this week?
🌍 Researcher: One big story this week: ... (source: https://...)
               🔧 web_search({"query": "AI news this week"})

You:          Add a task: redo project 05 this weekend
✅ Organizer:  Done! I added task #1: Redo project 05 this weekend.
               🔧 list_tasks({}) · add_task({"title": "Redo project 05 this weekend"})
```
And the to-do panel now shows `#1 ⬜ Redo project 05 this weekend`. The small 🔧 line under each answer is the list of tools that specialist used: check that it makes sense for the question.

## How it works
```
 browser (page.html) ──► app.py (FastAPI) ──► assistant.handle(message, history)
                                                 ├─ Receptionist: ai.ask_for_data → Route (which specialist?)
                                                 └─ Specialist: agent.py loop + its own tools
                                                      ├─ 📚 search_my_documents → Chroma vector database (docs/ + uploads)
                                                      ├─ 🌍 Claude's web search
                                                      ├─ ✅ add_task / list_tasks / finish_task → SQLite (tasks.db)
                                                      └─ 💬 no tools, just conversation
```
**`assistant.py`, the brain:**
1. **📚 Librarian's database.** `library` is a Chroma collection saved in `chroma_data`. `add_document(path)` reads a PDF (page by page with `pypdf`) or a text file, cuts it into paragraphs (and long paragraphs into ~500-character pieces at a space), removes the file's old chunks, and stores the new ones with a `source` label. `search_my_documents(question)` returns the 4 closest chunks, each starting with `[file name]` so the Librarian can say where the answer came from.
2. **✅ Organizer's database.** `tasks.db` is a SQLite file with one table, `tasks` (`id`, `title`, `done`), exactly like Part 1's to-do API. `add_task`, `list_tasks` and `finish_task` are the tools. `finish_task` checks `rowcount` so it can say "There is no task #99" instead of pretending.
3. **The team.** `TEAM` maps each specialist name to three things: its instructions, its tools, and whether it may use web search. `Route` uses `Literal[...]` so the receptionist can only pick one of the four names.
4. **`handle(message, history)`** first asks the receptionist (with the last 4 messages, so follow-ups route correctly), then builds a short "Conversation so far" from the last 6 messages and runs the chosen specialist with `run_agent(..., show=False, trace=used)`. `trace` collects every tool call (including web searches) so the page can show them. It returns the specialist's name, the reply and the tools used.
5. At the bottom, every `.md`, `.txt` and `.pdf` in `docs/` is loaded when the app starts.

**`app.py`, the API:** `POST /chat` calls `assistant.handle` and saves the exchange in `history` (one shared conversation, kept in memory). `POST /upload` saves a file into `docs/` (only `.pdf`, `.txt`, `.md`) and adds it to the library straight away. `GET /tasks` returns the to-do list for the side panel. `GET /` serves the page.

**`page.html`, the face:** `ask(text)` shows your message, posts it to `/chat`, and shows the reply with the specialist's name and a 🔧 line of tools. After every answer it calls `refreshTasks()`, so the to-do panel updates live.

**You understand every piece of this.** That's the point of the whole course.

## If something goes wrong
- **The chat says "⚠️ Something went wrong"** → look at the terminal running uvicorn. `ANTHROPIC_API_KEY is not set` means: stop the server (`Ctrl + C`), set the key in that terminal, start again.
- **`RuntimeError: Form data requires "python-multipart" to be installed`** → run `pip install python-multipart`.
- **`[Errno 48] Address already in use`** (or 98/10048) → lesson 25's server (or another) is still running on port 8000. Stop it, or run `uvicorn app:app --reload --port 8001` and open http://127.0.0.1:8001.
- **The wrong specialist answers** (e.g. a question about your CV goes to 🌍) → the receptionist guessed wrong. Mention "my documents" or "my CV" in your message, or make the routing rules in `handle()` more specific.
- **You want a fresh start** → stop the server and delete `tasks.db` (empties the to-do list) and/or the `chroma_data` folder (forgets uploaded documents; files still in `docs/` are loaded again on start).

## Make it yours
Pick at least two:
1. Put your own notes and PDFs in `docs/` (and delete the sample `expense_policy.md` if you like), so it becomes *your* knowledge assistant.
2. Add a 5th specialist: a 🌦️ **Weather** agent using `get_weather` from lesson 28.
   <details><summary>Solution</summary>

   In `assistant.py`, add `import httpx` at the top and copy the `get_weather` function from lesson 28's `assistant.py`. Then:
   ```python
   class Route(BaseModel):
       specialist: Literal["librarian", "researcher", "organizer", "chatter", "weather"]
   ```
   Add to `TEAM`:
   ```python
   "weather": ("You tell the user the current weather. Use the tool, then answer in one friendly sentence.",
               [tool(get_weather, "Current temperature in a city", {"city": ("string", "City name")})], False),
   ```
   Add `'weather' = current weather or temperature;` to the routing rules in `handle()`, and in `page.html` add `weather:"🌦️ Weather"` to `ICON`.
   </details>
3. Add a `delete_task(task_id)` tool so the Organizer can remove tasks, not just finish them.
   <details><summary>Hint</summary>

   Copy `finish_task` and change the SQL to `DELETE FROM tasks WHERE id = ?`. Then add `tool(delete_task, "Delete a task", {"task_id": ("integer", "task number")})` to the Organizer's tool list.
   </details>
4. Deploy it online with the Dockerfile pattern from [05 · Put your API on the internet](../../part-1-apis/05-put-your-api-on-the-internet), and put the link and a 1-minute demo video on your CV and LinkedIn.
   <details><summary>Hint</summary>

   Make a `requirements.txt` with the Part 6 packages, copy *all* the files (`COPY . .` instead of `COPY main.py .`), and change `main:app` to `app:app` in the `CMD` line. Set `ANTHROPIC_API_KEY` in your host's **environment variables** settings, never in a file. Anyone with the link can use your key, so set a low monthly spend limit in the Claude Console first.
   </details>

### Your finished project checklist
Your assistant is "done" (and portfolio-ready) when you can tick every box:
- [ ] `uvicorn app:app --reload` starts with no errors, and the page opens at http://127.0.0.1:8000.
- [ ] All four specialists answer correctly at least once: 📚 a question about your docs, 🌍 a news question, ✅ add + show + finish a task, 💬 small talk.
- [ ] Every 📚 answer names the file it came from, and a question your documents can't answer gets "I couldn't find that" instead of a made-up answer.
- [ ] You uploaded at least one document of your own (notes, CV, a manual) and asked about it successfully.
- [ ] Follow-ups work: after a to-do answer, "now mark it as done" goes to the Organizer and finishes the right task.
- [ ] The to-do list survives a restart (stop the server, start it again, the tasks are still there).
- [ ] You made at least two "Make it yours" changes.
- [ ] Your API key is not in any file you share (`git status` / your GitHub repo shows no key).
- [ ] You can explain the "How it works" diagram out loud in two minutes, without notes.
- [ ] (Stretch) It's online with a link, and you recorded a 1-minute demo video.

## Try this
1. Ask the 💬 Chatter for a study tip, then say `add that as a task`. Which specialist handles the second message, and does it add the right thing?
   <details><summary>Hint</summary>

   The receptionist sees the last 4 messages, so it should route to ✅ Organizer, and the Organizer gets the conversation so far, so it knows what "that" is. This is why `handle()` passes `history` to both.
   </details>
2. Ask the 📚 Librarian something your documents don't cover, like `What's my manager's phone number?`. Does it admit it doesn't know?
   <details><summary>Hint</summary>

   It should say your documents don't contain it, because its instructions say "If they don't contain the answer, say so." If it guesses instead, make that sentence stronger, as you did with `RULES` in lesson 24.
   </details>
3. Show how long each answer took: when the reply arrives, add the time to the specialist's name (e.g. `📚 Librarian · 3.2 s`).
   <details><summary>Solution</summary>

   In `page.html`, inside `ask(text)`, record the start time at the very beginning, then add the seconds to the name label:
   ```javascript
   const start = Date.now();
   // ... after `const d=await r.json();`
   const secs = ((Date.now() - start) / 1000).toFixed(1);
   bubble("bot", d.reply, ICON[d.specialist] + " · " + secs + " s", d.tools_used);
   ```
   (Replace the existing `bubble("bot", d.reply, ICON[d.specialist], d.tools_used);` line.) You'll notice 🌍 web answers take the longest: searching the web is slow.
   </details>

## Check yourself
1. Follow one message, `Add 'buy milk' to my list`, from the browser to the database and back. Which files and functions does it pass through?
2. Why does each specialist get only some of the tools, instead of one agent with all of them?
3. Where do your documents live, and where do your tasks live? Why two different databases?
4. What would you change first to let several different people use this app at the same time?

<details><summary>Answers</summary>

1. `page.html` `ask()` → `POST /chat` in `app.py` → `assistant.handle()` → the receptionist (`ai.ask_for_data` → `organizer`) → `run_agent` with the Organizer's tools → Claude asks for `add_task` → SQLite `INSERT` in `tasks.db` → the result goes back to Claude → reply → `app.py` saves it in `history` → JSON back to the page → `refreshTasks()` calls `GET /tasks` and the panel updates.
2. Focused agents are more accurate (fewer tools to choose from, shorter instructions) and safer (the Chatter can't delete your tasks or search your private files).
3. Documents are in Chroma (`chroma_data`), because you search them by meaning. Tasks are in SQLite (`tasks.db`), because you need exact rows with ids and a done/not-done column. Use the right database for each kind of data.
4. Give each user their own `history` (like lesson 25's `chat_id`), their own tasks (a `user` column) and their own documents (a `user` label in the metadata), plus a login.
</details>

## Learn more (optional)
- [Anthropic: Building effective agents](https://www.anthropic.com/engineering/building-effective-agents)
- [Claude docs: tool use overview](https://platform.claude.com/docs/en/agents-and-tools/tool-use/overview)
- Video search: [AI engineer portfolio project ideas](https://www.youtube.com/results?search_query=ai+engineer+portfolio+projects)

## Next
🎉 **You've finished AI from Zero!** You went from "what is Python?" to a multi-agent app with RAG, web search and a database. Where to go now:
- → [Voice AI from Zero](../../../voice-ai-from-zero): give your assistant ears and a voice, with free open-source models that run on your own computer.
- → [AI Engineer Journey](../../../ai-engineer-journey): deeper versions of everything you've done (evaluating AI quality, monitoring, MCP servers, fine-tuning, building a GPT from scratch).

Whichever you choose, keep building your own assistant on the side: a project you keep improving is the best thing to show an employer.
