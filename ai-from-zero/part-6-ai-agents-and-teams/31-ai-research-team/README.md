# 31 · AI research team

**What you'll build:** give it any topic. A **planner AI** splits it into 3 questions, three **researcher AIs** search the live web *at the same time*, and a **writer AI** combines their notes into a report with sources, saved as `report.md`.
**Time:** ~1 hour · **Builds on:** [28 · Agent with many tools](../28-agent-with-many-tools) (web search) and [30 · AI customer-support team](../30-ai-customer-support-team) (a team of AIs) · **Needs:** an Anthropic API key and an internet connection

## Why this matters
Big jobs go faster and come out better when you **split them up**: one AI plans, several work in parallel, and one puts the results together. This is how "deep research" features in AI products work, and the same plan → fan out → combine pattern is used to process many documents, compare many products, or review many files at once.

## What you'll learn
- **Planner / workers / writer:** a common multi-agent design (often called "orchestrator-workers").
- **Parallel work:** `ThreadPoolExecutor` runs the three researchers at the same time instead of one after another.
- **Focused context:** each researcher only sees its own question, so it stays on topic; the writer only sees the finished notes.
- **Grounded report:** the writer is told to use only facts from the notes and to list the sources.

## Before you start
- Install the Part 6 packages (once):
  ```bash
  pip install anthropic chromadb pypdf fastapi "uvicorn[standard]" python-multipart httpx tzdata
  ```
  This lesson only needs `anthropic` (Claude, including its built-in web search).
- Set your API key in this terminal (full steps in the [Part 4 README](../../part-4-chatbots)):
  ```bash
  export ANTHROPIC_API_KEY=sk-ant-your-key-here        # Mac
  $env:ANTHROPIC_API_KEY="sk-ant-your-key-here"        # Windows PowerShell
  ```
- Cost: one run is 5 or more requests to Claude plus up to 9 web searches (3 per researcher). It's a few cents, but don't run it in a loop.

## Run it
1. From the course folder (`Learning/ai-from-zero`), with your venv switched on:
   ```bash
   cd part-6-ai-agents-and-teams/31-ai-research-team
   python research_team.py
   ```
2. Research your own topic:
   ```bash
   python research_team.py "Which electric cars under 35,000 euros have the best range in 2026?"
   ```
3. Open `report.md` (it appears in this folder). VS Code shows it nicely formatted: right-click the file → **Open Preview**.

### What you should see
```
🗺️  Plan:
   • Which technical skills do job adverts for junior AI engineers ask for most in 2026?
   • Which non-technical skills help junior AI engineers get hired?
   • What are the best free courses and resources to learn these skills?

🔎 Researching all questions at the same time...

# Skills for junior AI engineers in 2026

## Summary
...

## Sources
- https://...

📄 Saved to report.md
```
The plan appears within seconds; the research step takes the longest (often 30–90 seconds), because each researcher searches the web several times. Your questions, report and sources will differ every run. Check that the sources in the report are real links you can open.

## How it works
```
topic ──► PLANNER ──► 3 questions ──┬──► researcher 1 (web search) ──┐
                                     ├──► researcher 2 (web search) ──┼──► notes ──► WRITER ──► report.md
                                     └──► researcher 3 (web search) ──┘
                                          (all three at the same time)
```
1. **Planner.** `class Plan(BaseModel)` is a form with one field, a list of questions. `ai.ask_for_data(..., Plan, ...)` asks Claude to split the topic into exactly 3 focused questions and returns them as a real Python list.
2. **Researchers.** `research(question)` runs one agent (`run_agent` from `agent.py`) with `web_search=True`, no other tools, and `show=False` so the three don't print over each other. Its instructions ask for 5 short facts, each with a source link.
3. **At the same time.** `with ThreadPoolExecutor() as pool:` creates a small group of workers, and `pool.map(research, plan.questions)` gives each question to a worker. They all wait for Claude in parallel, so 3 researchers take about as long as 1. `list(...)` collects the results in the same order as the questions.
4. **Joining notes.** `all_notes` glues each question (as a `## heading`) and its notes into one text.
5. **Writer.** `ai.ask(...)` with a system prompt for clear, beginner-friendly reports (summary, sections, sources) that uses **only** facts from the notes. `max_tokens=8000` leaves room for a long report.
6. `open("report.md", "w", encoding="utf-8")` saves the report; `encoding="utf-8"` makes sure special characters (é, €, emoji) save correctly on every computer.

## If something goes wrong
- **It sits on "Researching..." for a long time** → normal: web research is slow. Give it up to 2–3 minutes. If it never finishes, press `Ctrl + C` and check your internet connection.
- **The report says some research failed, or a researcher's notes say `Stopped: too many steps.`** → that question was too broad. Make your topic more specific and run again.
- **An error mentioning `web_search`** → web search may need to be enabled for your organisation in the Claude Console (Settings). See lesson 28's troubleshooting.
- **`anthropic.RateLimitError`** → three researchers at once can hit your account's rate limit on a new account. Wait a minute, or limit the workers with `ThreadPoolExecutor(max_workers=1)` (slower, but one at a time).
- **`❌ ANTHROPIC_API_KEY is not set`** → set the key in this terminal.

## Try this
1. Ask the planner for 5 questions instead of 3. Does the report get better? Is it slower?
   <details><summary>Hint</summary>

   Change `"Split it into exactly 3 focused research questions."` to `5`, and the comment in `Plan`. Because the researchers work in parallel, it takes only a little longer, but it costs more and the report gets longer. More isn't always better: overlapping questions repeat the same facts.
   </details>
2. Time it: add `import time` at the top, `start = time.time()` before the `with ThreadPoolExecutor()` line, and `print(f"Research took {time.time() - start:.0f} seconds")` after it. Then replace the `with` block with a normal loop, `notes = [research(q) for q in plan.questions]`, and compare.
   <details><summary>Hint</summary>

   The normal loop runs the researchers one after another, so it takes roughly 3× as long. That's why parallel work matters for agents: most of the time is spent *waiting* for the AI, and waiting can happen at the same time.
   </details>
3. Add a 4th AI, a **fact checker**, that reads the report and the notes and lists any claim in the report that isn't backed by the notes.
   <details><summary>Solution</summary>

   Add this at the end of the file:
   ```python
   # 4. FACT CHECKER
   check = ai.ask(f"Research notes:\n{all_notes}\n\nReport:\n{report}\n\nList every claim in the report that is NOT "
                  "supported by the notes. If all claims are supported, say 'All claims are supported.'",
                  system="You are a careful fact checker. Be specific and brief.")
   print(f"\n🔍 Fact check:\n{check}")
   ```
   This is the writer-and-critic idea from lesson 29, used for accuracy instead of style.
   </details>

## Check yourself
1. What are the three roles in this team, and what does each one do?
2. Why are the researchers run with `ThreadPoolExecutor` instead of a normal `for` loop?
3. Why does each researcher only get its own question, and not the whole topic and the other questions?
4. How does the writer avoid making things up?

<details><summary>Answers</summary>

1. The planner splits the topic into questions; the researchers each search the web for one question; the writer combines all notes into a report.
2. So they work at the same time. Each one spends most of its time waiting for Claude and the web, so running them in parallel makes the whole job about 3× faster.
3. A small, focused task gives better, more on-topic results, and keeps each request short and cheap.
4. Its instructions say to use only facts from the research notes, and to list the sources. (The fact checker in exercise 3 adds a second check.)
</details>

## Learn more (optional)
- [Anthropic: Building effective agents](https://www.anthropic.com/engineering/building-effective-agents) (see "orchestrator-workers" and "parallelization")
- [Python docs: concurrent.futures](https://docs.python.org/3/library/concurrent.futures.html)

## Next
→ [32 · Final project: your personal AI assistant](../32-final-project-your-personal-ai-assistant)
