# 8.4 · Data analyst agent: text-to-SQL with a reviewer

**What you build:** ask business questions in plain English ("revenue per month?", "which product gets refunded most?"). An **Analyst agent** explores a real SQLite database, writes SQL, and draws **charts**. Every query is first checked by a **Reviewer agent** that catches classic mistakes (double counting, forgetting to exclude refunded orders) and fixes them before execution.
**Like you're 10:** the analyst is a kid who's great at asking the shop's computer questions, but before any question goes in, a careful grown-up reads it and says "wait, you forgot to skip the cancelled orders!" And the computer is in **read-only mode**: nobody can delete anything, even by accident.

## Run it
```bash
cd level-8-multi-agent-systems/04-data-analyst-agent-text-to-sql
pip install -r requirements.txt
python make_db.py                     # creates shop.db (400 customers, 2,000 orders)
export ANTHROPIC_API_KEY=sk-ant-...
python analyst.py
python analyst.py "Which customers signed up in 2025 but never ordered in 2026?"
```
Charts are saved as PNG files in this folder.

Tests (offline): `pytest -v`

## Key ideas
- **Text-to-SQL** is one of the most valuable enterprise AI uses: everyone can query data without knowing SQL.
- **Three layers of safety (defence in depth):**
  1. `is_safe_select`: only a single SELECT is allowed,
  2. the SQLite connection is opened **read-only** (`mode=ro`), so the database refuses writes anyway,
  3. the **Reviewer agent** checks query *logic* before it runs.
- **Agent as a tool:** the Reviewer is called *inside* the `run_sql` tool, so the Analyst can't skip review.
- **Schema in the prompt** plus `describe_table` for exploring: models write far better SQL when they see column names and sample rows.
- **Correctness ≠ runs without error:** a query that double-counts revenue runs fine and is still wrong. That's why the reviewer exists.

## Your turn
1. Write 10 questions with known correct answers (compute them yourself in SQL) and measure the analyst's accuracy (7.5 style).
2. Add a `forecast_next_month` tool using linear regression from Level 3 on the monthly revenue.
3. Point it at a different SQLite database, e.g. the Chinook music store sample: https://github.com/lerocha/chinook-database

## Read
- Text-to-SQL best practices: https://www.youtube.com/results?search_query=text+to+sql+LLM+agent+best+practices
