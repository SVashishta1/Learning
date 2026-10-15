# 8.3 · Research team: planner, parallel researchers, writer, fact-checker

**What you'll build:** a team that researches any topic on the live web and writes a **cited report**:
1. a **Planner** splits the topic into 3–5 sub-questions (structured output),
2. **Researchers run in parallel**, each using Claude's built-in **web search**,
3. a **Writer** combines their notes into a Markdown brief with numbered citations,
4. a **Fact-checker** flags claims the notes don't support, and the Writer fixes them.

**Like you're 10:** a school project. The team captain splits the topic ("you do history, you do science, you do pictures"), everyone researches *at the same time*, one person writes the poster, and the strictest friend checks that every fact has a source before it goes on the wall.
**Time:** ~2 h · **Builds on:** [8.2 Customer-support team](../02-customer-support-router-and-specialists) and web search from [7.4](../../level-7-real-world-ai-apps/04-ai-agent-with-tools-calculator-weather-search) · **Needs:** an Anthropic API key (tests run without one)

## Why this matters
"Research this and write me a brief" is a task people pay analysts, consultants and journalists for, and it's one of the most useful things AI teams do today. A single agent doing everything gets slow and loses focus as its context fills with search results. Splitting the work (plan → research in parallel → write → check) is faster, cheaper per useful word, and more reliable. Anthropic's own Research feature uses this architecture.

## What you'll learn
- **Orchestrator-workers pattern**: one planner decides the sub-tasks, many workers do them, one writer combines the results.
- **Parallelism with threads**: `ThreadPoolExecutor` runs the researchers at the same time, so 4 take about as long as 1.
- **Context isolation**: each researcher has its own small conversation, and the writer only sees their distilled notes.
- **Server tools**: web search runs on Anthropic's servers; `max_uses` caps how many searches each researcher can do.
- **Verification step**: a fact-checker compares the report with the notes and sends problems back for fixing.

## Before you start
```bash
cd level-8-multi-agent-systems/03-research-team-planner-researchers-writer
pip install -r requirements.txt
```
- `anthropic`: calls Claude (including web search). `pydantic`: the `Plan` and `FactCheck` schemas. `pytest`: tests.

**API key:** set `ANTHROPIC_API_KEY` as in the [Level 7 README](../../level-7-real-world-ai-apps/README.md#api-key-needed-from-here-on). Web search is billed per search on top of tokens; `max_uses: 4` per researcher keeps it to a few cents. Cheap mode: `export CLAUDE_MODEL=claude-haiku-5-5`.

## Run it
1. From the course root: `cd level-8-multi-agent-systems/03-research-team-planner-researchers-writer`
2. Tests (offline): `pytest -v`
3. Default topic (in-demand AI engineering skills): `python research_team.py`
4. Your own topic: `python research_team.py "Compare vector databases (pgvector, Chroma, Pinecone) for a startup's RAG app"`

### What you should see
(Shortened and representative; a real run takes 1–3 minutes and the report is much longer.)
```
[Planner] 📋 Plan: sub_questions=['Which AI engineering skills appear most in 2026 job postings?', 'Which programming and data skills do employers expect from ...
[Researcher-1] ▶ Which AI engineering skills appear most in 2026 job postings?
[Researcher-2] ▶ Which programming and data skills do employers expect from junior AI engineers?
[Researcher-3] ▶ What free courses and projects help beginners learn these skills?
[Researcher-3] ✔ done (1840 chars)
[Researcher-1] ✔ done (2215 chars)
[Researcher-2] ✔ done (1960 chars)
[Writer] ▶ Topic: What are the most in-demand skills for AI engineers in 2026, and how can a beginner learn them? ...
[Writer] ✔ done (3104 chars)
[FactChecker] 📋 FactCheck: unsupported_claims=["'80% of postings require Kubernetes' is not in the notes"] missing_citations=[] verdict='needs_fixes'
[Writer] ▶ <research_notes> ...
[Writer] ✔ done (3010 chars)

**Summary.** Employers want Python, APIs, RAG and evals [1][2]. ...

Saved report.md

Token usage per agent:
  Planner                    210 in /    150 out  ≈ $0.0038
  Researcher-1             18400 in /    900 out  ≈ $0.0916
  ...
  TOTAL                  ≈ $0.3410
```
What to look at: the three researchers start together and finish in any order (that's parallelism); the fact-checker caught a claim the notes didn't support and the Writer removed it; the cost report shows researchers use the most input tokens, because web search results are long.

## How it works
```
topic ─► Planner.ask_structured(Plan) ─► [q1, q2, q3]
             ┌──────────────┬──────────────┐   (threads, at the same time)
        Researcher-1   Researcher-2   Researcher-3   each: web_search → bullet notes with URLs
             └──────────────┴──────────────┘
                       notes ─► Writer ─► report ─► FactChecker(FactCheck) ─► needs_fixes? ─► Writer fixes
```

1. **Schemas.** `Plan` has `sub_questions` (3–5, specific, non-overlapping) and `audience`. `FactCheck` lists `unsupported_claims` and `missing_citations`, and a `verdict` that can only be `"pass"` or `"needs_fixes"`.
2. **`make_team()`** creates the Planner (`effort="low"`: planning is quick), the Writer (strict Markdown format, every fact cited like `[1]`, use ONLY the notes) and the FactChecker.
3. **`web_search_tool(model)`** returns the server-tool definition with `max_uses: 4`, choosing the newest search version for Opus/Sonnet and the basic one for Haiku.
4. **`research(question, n)`** creates a fresh `Researcher-n` agent with that tool and asks it for bullet-point notes with a URL after each bullet. A fresh agent per question means each one's context holds only its own searches.
5. **`run(topic)`**: the Planner makes the `Plan`; at most 5 questions are kept. `ThreadPoolExecutor` submits one `research()` per question; `f.result()` waits for each. The notes are joined under `## question` headings and given to the Writer inside `<research_notes>` tags.
6. **The check.** The FactChecker reads the notes and the report. If the verdict isn't `pass` and it listed problems, the Writer gets the notes, its report and the problem list, and must remove or correctly cite each one. `run()` returns the final report and every agent (for the cost report).
7. **`__main__`** saves `report.md` and prints `cost_report()`.
8. **`test_research_team.py`** uses a `RoutingFake` that answers based on *which* agent is asking (threads make the call order unpredictable). It checks 3 researchers ran with web search and that the Writer saw all sub-questions.

## If something goes wrong
- **`anthropic.AuthenticationError`** → set `ANTHROPIC_API_KEY` in this terminal.
- **An error mentioning `web_search`** → web search may be disabled for your organisation in the Claude Console (Settings → Privacy/Features), or unavailable for your model. Enable it, or try the default model.
- **`anthropic.RateLimitError` (429)** → several researchers call the API at once, and new accounts have low limits. Run again after a minute, or reduce parallelism with `ThreadPoolExecutor(max_workers=2)`.
- **The report has no citations or invents facts** → read `FactCheck` in the log. Make the Writer's rules stricter, or run a second check round (see *Try this*).
- **It costs more than you expected** → the cost report shows where. Lower `max_uses`, use Haiku for researchers (`model="claude-haiku-5-5"` in `research()`), or plan fewer sub-questions.

## Try this
1. **Let the planner size the team.** Change `Plan` so the Planner chooses 1 sub-question for a simple topic and up to 5 for a broad one. Try "What is the capital of Australia?" vs. "Compare the AI policies of the EU, US and China".
   <details><summary>Hint</summary>

   Change the field description to "1 to 5 questions: 1 for a simple factual topic, up to 5 for broad comparisons" and add to the Planner's system prompt "Use as few sub-questions as the topic really needs". Watch the cost report: fewer researchers, much cheaper.
   </details>
2. **Read whole pages.** Give researchers Claude's `web_fetch` server tool so they can read a full article, not just search snippets.
   <details><summary>Solution</summary>

   In `research()`:
   ```python
   fetch = {"type": "web_fetch_20250910" if "haiku" in llm.MODEL else "web_fetch_20260209",
            "name": "web_fetch", "max_uses": 2}
   agent = Agent(..., server_tools=[web_search_tool(llm.MODEL), fetch], ...)
   ```
   and add to the researcher's prompt "Fetch the most relevant page when snippets aren't enough". Web fetch can only open URLs that already appeared in the conversation (e.g. from search results), which stops it wandering off. Expect better notes and more input tokens.
   </details>
3. **An Editor for younger readers.** Add a final `Editor` agent that rewrites the report for a 12-year-old, keeping the citations. Save it as `report_simple.md` and compare.
   <details><summary>Solution</summary>

   In `__main__`, after `report, agents = run(topic)`:
   ```python
   editor = Agent("Editor", "You rewrite reports for 12-year-olds: short sentences, everyday words, "
                            "one example per idea. Keep every [n] citation and the Sources list.")
   simple = editor.run(f"<report>\n{report}\n</report>\n\nRewrite this report.")
   Path("report_simple.md").write_text(f"# {topic} (simple version)\n\n{simple}\n", encoding="utf-8")
   agents.append(editor)
   ```
   This is the "pipeline" pattern: a fixed extra step after the team finishes.
   </details>

## Check yourself
1. Why are the researchers separate agents instead of one agent doing all the searches?
2. Running 4 researchers in parallel: does it make the run faster, cheaper, or both?
3. Why does the Writer receive notes instead of the raw search results?
4. What does the fact-checker protect the reader from?

<details><summary>Answers</summary>

1. Each gets a small, focused context with only its own question and results, so it stays on topic. They can also run at the same time, and one failing doesn't spoil the others.
2. Faster (wall-clock time is roughly that of the slowest researcher), not cheaper: every researcher still uses its own tokens, so cost adds up.
3. Raw results are long and noisy. Distilled notes keep the Writer's prompt short (cheaper) and focused on the facts that matter (better quality).
4. Hallucinated or uncited claims: sentences that sound right but aren't supported by any source the team actually found.
</details>

## Learn more (optional)
- How we built our multi-agent research system (Anthropic): https://www.anthropic.com/engineering/multi-agent-research-system
- Tool use, including web search: https://platform.claude.com/docs/en/agents-and-tools/tool-use/overview
- Python threads and ThreadPoolExecutor: https://docs.python.org/3/library/concurrent.futures.html

## Next
→ [8.4 · Data analyst agent: text-to-SQL with a reviewer](../04-data-analyst-agent-text-to-sql)
