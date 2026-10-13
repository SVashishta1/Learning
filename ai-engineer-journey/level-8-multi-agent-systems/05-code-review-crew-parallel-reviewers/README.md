# 8.5 · Code review crew: parallel reviewers + a lead

**What you build:** an automated code reviewer staffed by **three specialist agents** (Security, Correctness, Maintainability) that review the same code **in parallel**, each returning findings in a strict schema. A **Lead reviewer** then merges, de-duplicates and ranks everything into one Markdown report with a merge recommendation. It ships with a deliberately terrible file to review (SQL injection, hardcoded secret, `pickle`, `os.system`, a swallowed exception, an O(n²) loop...).
**Like you're 10:** three teachers mark the same essay at the same time: one only checks spelling, one only checks facts, one only checks handwriting. The head teacher collects the three marked copies, removes repeated comments, and writes one final report card.

## Run it
```bash
cd level-8-multi-agent-systems/05-code-review-crew-parallel-reviewers
pip install -r requirements.txt
export ANTHROPIC_API_KEY=sk-ant-...
python review_crew.py sample_code/user_service.py
python review_crew.py ../04-data-analyst-agent-text-to-sql/analyst.py   # review real code
python review_crew.py --diff                                            # review your uncommitted changes
```
The report is printed and saved to `review.md`.

Tests (offline): `pytest -v`

## Key ideas
- **Parallel specialists beat one generalist:** a narrow focus ("ONLY security") finds more issues in that area.
- **Structured findings** (line, severity, fix) let code sort, filter and render results, or post them as GitHub PR comments.
- **The aggregator** is a separate agent with a different job: judgement, not discovery.
- **Line numbers in the prompt** (`numbered()`) make findings precise.
- This is the same architecture used by commercial AI code reviewers.

## Your turn
1. Post the findings as comments on a GitHub pull request using the GitHub API.
2. Add a "Fixer" agent that takes the report and writes a corrected file. Then run the crew again on the fixed version: does the score improve?
3. Add a "Test-writer" agent that writes `pytest` tests for every bug it found.

## Read
- OWASP Top 10 (what the security reviewer hunts for): https://owasp.org/www-project-top-ten/
- Parallelization pattern: https://www.anthropic.com/engineering/building-effective-agents
