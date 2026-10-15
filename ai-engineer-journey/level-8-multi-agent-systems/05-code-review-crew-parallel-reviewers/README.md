# 8.5 · Code review crew: parallel reviewers + a lead

**What you'll build:** an automated code reviewer staffed by **three specialist agents** (Security, Correctness, Maintainability) that review the same code **in parallel**, each returning findings in a strict schema. A **Lead reviewer** then merges, de-duplicates and ranks everything into one Markdown report with a merge recommendation. It ships with a deliberately terrible file to review (SQL injection, a hardcoded secret, `pickle`, `os.system`, a swallowed exception, an O(n²) loop...).
**Like you're 10:** three teachers mark the same essay at the same time: one only checks spelling, one only checks facts, one only checks handwriting. The head teacher collects the three marked copies, removes repeated comments, and writes one final report card.
**Time:** ~2 h · **Builds on:** [8.4 Data analyst agent](../04-data-analyst-agent-text-to-sql) and parallel agents from [8.3](../03-research-team-planner-researchers-writer) · **Needs:** an Anthropic API key (tests run without one); `git` only for `--diff`

## Why this matters
AI code review is now a standard part of software teams: it runs on every pull request and catches security holes and bugs before a human even looks. Commercial AI reviewers use this same architecture: several focused reviewers, structured findings, and an aggregator. The pattern ("parallelization": same input, different specialists, then combine) works far beyond code, for example to review contracts, check essays or screen applications.

## What you'll learn
- **Parallelization pattern**: several agents examine the *same* input from different angles at the same time.
- **Specialists vs. a generalist**: a narrow focus ("ONLY security") finds more issues in that area.
- **Structured findings**: line, severity, why it matters and a fix, which code can sort, filter, render or post to GitHub.
- **Aggregator agent**: a lead whose job is judgement (merge, de-duplicate, rank, decide), not discovery.
- **Grounding with line numbers**: numbering the code so every finding points to an exact line.

## Before you start
```bash
cd level-8-multi-agent-systems/05-code-review-crew-parallel-reviewers
pip install -r requirements.txt
```
- `anthropic`: calls Claude. `pydantic`: the `Finding`, `Findings` and `FinalReport` schemas. `pytest`: tests.

**API key:** set `ANTHROPIC_API_KEY` as in the [Level 7 README](../../level-7-real-world-ai-apps/README.md#api-key-needed-from-here-on). Cheap mode: `export CLAUDE_MODEL=claude-haiku-5-5`.

## Run it
1. From the course root: `cd level-8-multi-agent-systems/05-code-review-crew-parallel-reviewers`
2. Tests (offline): `pytest -v`
3. Review the bad sample: `python review_crew.py sample_code/user_service.py`
4. Review real code: `python review_crew.py ../04-data-analyst-agent-text-to-sql/analyst.py`
5. Review your uncommitted changes (inside a git repo): `python review_crew.py --diff`

The report is printed and saved to `review.md`.

### What you should see
(Representative: the exact findings and wording vary run to run.)
```
[Correctness-Reviewer] 📋 Findings: findings=[Finding(line=16, severity='medium', title='Division by zero on empty list', ...
[Maintainability-Reviewer] 📋 Findings: findings=[Finding(line=30, severity='low', title='O(n²) duplicate search', ...
[Security-Reviewer] 📋 Findings: findings=[Finding(line=9, severity='critical', title='SQL injection in get_user', ...
[Lead-Reviewer] 📋 FinalReport: summary='This file has two critical injection vulnerabilities (SQL and shell), a leaked secret ...

# Code review: user_service.py

**Recommendation:** `request_changes`

This file has two critical injection vulnerabilities (SQL and shell), a leaked secret and unsafe deserialization. It must not be merged until these are fixed.

| # | Severity | Line | Issue |
|---|----------|------|-------|
| 1 | 🔴 critical | 9 | SQL injection in get_user |
| 2 | 🔴 critical | 28 | Command injection via os.system |
| 3 | 🟠 high | 4 | Hardcoded API secret |
| 4 | 🟠 high | 19 | Unsafe pickle.loads on untrusted data |
| 5 | 🟡 medium | 16 | Division by zero on empty list |
| 6 | 🟡 medium | 24 | Bare except swallows errors |
| 7 | 🔵 low | 30 | O(n²) duplicate search |

### 1. SQL injection in get_user
*Why it matters:* A username like `' OR '1'='1` returns other users' data.

*Fix:* Use a parameterised query: `cur.execute('SELECT * FROM users WHERE name = ?', (username,))`.
...
Saved review.md
```
What to look at: the three reviewers finish in any order (they run at the same time); each found different kinds of problems; the lead's table is sorted by severity and its line numbers match `sample_code/user_service.py`.

## How it works
```
code ─► numbered() ─┬─► Security-Reviewer ────────┐
                    ├─► Correctness-Reviewer ─────┼─► Findings × 3 ─► Lead-Reviewer ─► FinalReport ─► to_markdown() ─► review.md
                    └─► Maintainability-Reviewer ─┘   (in parallel)
```

1. **Schemas.** `Finding` = `line` (or none), `severity` (`critical`/`high`/`medium`/`low`, nothing else allowed), `title`, `why_it_matters` and a concrete `fix`. `Findings` is a list of them. `FinalReport` adds a `summary` and a `merge_recommendation` (`approve`, `approve_with_changes` or `request_changes`).
2. **`FOCUS`** maps each reviewer's area to exactly what it should hunt for. Each reviewer's system prompt says "ONLY for ..." and "not nitpicks outside your area": narrow jobs give deeper results.
3. **`numbered(code)`** prefixes every line with its number (`   9 | cur.execute(...)`), so the model can cite exact lines instead of guessing.
4. **`review(code)`** creates the three reviewers and runs `ask_structured(prompt, Findings)` for all of them at once with `ThreadPoolExecutor.map`. `pool.map` returns the results in the same order as the reviewers, whatever order they finish in.
5. **The Lead** gets the numbered code plus every finding as one JSON line tagged with the reviewer's name, and returns a `FinalReport`: duplicates merged, severities corrected if needed, most severe first, and a merge decision.
6. **`to_markdown(report, name)`** turns the report into a table (with coloured severity icons) followed by one section per finding with why and how to fix. Because findings are structured, this is plain Python, no LLM needed.
7. **`__main__`** reviews a file (default: the sample) or `git diff` output with `--diff`, saves `review.md` and prints `cost_report()` for all four agents.
8. **Tests** feed the crew scripted findings via `FakeClient`, check that the lead saw the reviewers' findings and the Markdown contains the icon and fix, and check `numbered()`.

## If something goes wrong
- **`Nothing to review.`** with `--diff` → you have no uncommitted changes, or you're not inside a git repository. Edit a file first, or review a file path instead.
- **`FileNotFoundError`** → the path is relative to where you run the command. From this folder, other lessons are at `../04-.../analyst.py`.
- **`anthropic.AuthenticationError`** → set `ANTHROPIC_API_KEY` in this terminal.
- **Line numbers are slightly off** → models occasionally miscount. Numbered input makes this rare; for very long files, review one file at a time.
- **Too many nitpicks** → make a reviewer's focus stricter, or tell the lead "drop low-severity style issues".

## Try this
1. **A fourth reviewer.** Add a "Documentation" reviewer that checks for missing docstrings, unclear names and confusing comments.
   <details><summary>Solution</summary>

   Add one entry to `FOCUS`:
   ```python
   "Documentation": "missing or misleading docstrings and comments, unclear function and variable names",
   ```
   That's it: `review()` creates one reviewer per entry and the thread pool grows automatically. Look at the cost report afterwards: every reviewer adds the whole file to its prompt.
   </details>
2. **A Fixer agent.** Add an agent that takes the code and the report and writes `user_service_fixed.py`, then run the crew on the fixed file. Did the recommendation improve?
   <details><summary>Solution</summary>

   At the end of `__main__`:
   ```python
   fixer = Agent("Fixer", "You fix code. Apply every critical and high finding, keep behaviour otherwise the same. "
                          "Output only the complete corrected Python file, no backticks.")
   fixed = fixer.run(f"<code>\n{code}\n</code>\n\n<review>\n{md}\n</review>")
   Path("user_service_fixed.py").write_text(fixed, encoding="utf-8")
   ```
   Then `python review_crew.py user_service_fixed.py`. This review → fix → re-review loop is 8.1's reflection pattern with a crew as the critic.
   </details>
3. **Post the review on a pull request.** With the GitHub CLI (`gh`, logged in) and a branch with an open PR, review the diff and post `review.md` as a PR comment.
   <details><summary>Hint</summary>

   `python review_crew.py --diff` reviews uncommitted changes; to review the PR's changes use `git diff main...HEAD` instead (change the `subprocess.run` list to `["git", "diff", "main...HEAD"]`). Then run `gh pr comment --body-file review.md`. Put both commands in a GitHub Actions workflow (like 7.6's CI) with `ANTHROPIC_API_KEY` stored as a repository secret, and every PR gets an AI review automatically.
   </details>

## Check yourself
1. Why three narrow reviewers instead of one prompt saying "review security, bugs and style"?
2. What does the Lead do that the reviewers can't?
3. Why number the lines before sending the code?
4. Does running the reviewers in parallel reduce the cost?

<details><summary>Answers</summary>

1. A narrow focus makes each agent look deeper in its area instead of skimming everything; one big prompt tends to find the obvious issues and miss the rest. They also run at the same time, so it isn't slower.
2. It sees all findings together, so it can merge duplicates (two reviewers may flag the same line), fix inconsistent severities, rank them and make one overall decision.
3. So findings point to exact lines. Models are bad at counting lines themselves, and a precise line makes a finding actionable (and postable as a GitHub line comment).
4. No. It reduces waiting time. Each reviewer still reads the whole file, so cost grows with the number of reviewers.
</details>

## Learn more (optional)
- OWASP Top 10 (what the security reviewer hunts for): https://owasp.org/www-project-top-ten/
- Building effective agents, parallelization pattern (Anthropic): https://www.anthropic.com/engineering/building-effective-agents
- GitHub CLI `gh pr comment`: https://cli.github.com/manual/gh_pr_comment

## Next
→ [8.6 · Build your own MCP server](../06-build-your-own-mcp-server)
