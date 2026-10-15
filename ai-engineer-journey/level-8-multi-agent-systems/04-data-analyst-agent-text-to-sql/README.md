# 8.4 · Data analyst agent: text-to-SQL with a reviewer

**What you'll build:** ask business questions in plain English ("revenue per month?", "which product gets refunded most?"). An **Analyst agent** explores a real SQLite database, writes SQL and draws **charts**. Every query is first checked by a **Reviewer agent** that catches classic mistakes (double counting, forgetting to exclude refunded orders) and fixes them before anything runs.
**Like you're 10:** the analyst is a kid who's great at asking the shop's computer questions, but before any question goes in, a careful grown-up reads it and says "wait, you forgot to skip the cancelled orders!" And the computer is in **read-only mode**: nobody can delete anything, even by accident.
**Time:** ~2.5 h · **Builds on:** [8.3 Research team](../03-research-team-planner-researchers-writer) and SQL from [1.5](../../level-1-apis/05-todo-api-with-sqlite-then-postgres) · **Needs:** an Anthropic API key (tests run without one)

## Why this matters
Most company knowledge lives in databases, and most people can't write SQL. "Ask your data in plain English" (text-to-SQL) is one of the most valuable enterprise AI features, built into BI tools and analytics copilots. It's also dangerous: a query can run perfectly and still be *wrong* (counting refunded orders as revenue), or try to change data. This lesson shows the professional answer: several layers of safety, including a second agent whose only job is to check the first.

## What you'll learn
- **Text-to-SQL**: an agent that explores a schema and writes SQL to answer a question.
- **Guardian (reviewer) agent**: a second agent that must approve or fix every query before it runs.
- **Defence in depth**: three independent safety layers (a SELECT-only filter, a read-only connection, the reviewer), so one failure isn't a disaster.
- **Agent inside a tool**: the reviewer is called *inside* `run_sql`, so the analyst can't skip it.
- **Correct vs. runs**: why "no error" doesn't mean "right answer".

## Before you start
```bash
cd level-8-multi-agent-systems/04-data-analyst-agent-text-to-sql
pip install -r requirements.txt
```
- `anthropic`: calls Claude. `pydantic`: tool inputs and the `Review` schema.
- `matplotlib`: draws the charts. `pytest`: tests. (`sqlite3` comes with Python.)

**API key:** set `ANTHROPIC_API_KEY` as in the [Level 7 README](../../level-7-real-world-ai-apps/README.md#api-key-needed-from-here-on). Cheap mode: `export CLAUDE_MODEL=claude-haiku-5-5`.

## Run it
1. From the course root: `cd level-8-multi-agent-systems/04-data-analyst-agent-text-to-sql`
2. Tests (offline): `pytest -v`
3. Build the database (400 customers, 12 products, 2,000 orders in 2026): `python make_db.py`
4. Ask the 3 built-in questions: `python analyst.py`
5. Ask your own: `python analyst.py "Which customers signed up in 2025 but never ordered in 2026?"`

Charts are saved as PNG files in this folder.

### What you should see
(The SQL and wording vary; the numbers come from the real `shop.db`.)
```
======================================================================
❓ What were total revenue and number of completed orders per month in 2026? Chart it.

[Analyst] ▶ What were total revenue and number of completed orders per month in 2026? Chart it.
[SQL-Reviewer] 📋 Review: approved=False problems=["Includes refunded and cancelled orders; revenue must count only status = 'completed'"] ...
[Analyst] 🔧 run_sql({"sql": "SELECT substr(o.order_date,1,7) AS month, SUM(oi.quantity*p.price) AS revenue, ...) -> (Reviewer fixed the query: [...])
month | revenue | orders
[SQL-Reviewer] 📋 Review: approved=True problems=[] corrected_sql=None
[Analyst] 🔧 make_chart({"sql": "SELECT substr(o.order_date,1,7) AS month, ...", ...}) -> Saved chart to revenue_by_month_2026.png
[Analyst] ✔ done (612 chars)
Revenue from completed orders in 2026:

| Month | Revenue | Orders |
|-------|---------|--------|
| 2026-01 | $46,967 | 210 |
| 2026-02 | $44,817 | 170 |
| 2026-03 | $55,218 | 234 |
| ...     | ...     | ... |
| 2026-09 | $52,841 | 196 |

Total: $452,767. March and July were the strongest months. Chart saved as revenue_by_month_2026.png.
```
What to look at: the Analyst's first query forgot the `status = 'completed'` filter. It would have *run fine* and over-reported revenue. The Reviewer caught it and the fixed query ran instead. Then the chart query was reviewed too, approved, and saved as a PNG.

## How it works
```
question ─► Analyst ──run_sql(sql, purpose)──► is_safe_select? ─► Reviewer.ask_structured(Review)
                │                                                   │ approved → run as is
                │                                                   │ fixable  → run corrected_sql
                │                                                   └ rejected → tell the Analyst why
                │                                       read-only SQLite (mode=ro) ─► rows ─► Analyst
                └─make_chart(sql, title, kind, filename)─► same review ─► matplotlib ─► PNG
```

1. **`make_db.py`** builds `shop.db` with a fixed random seed (same data for everyone): `customers`, `products`, `orders` (90% completed, 6% refunded, 4% cancelled) and `order_items`.
2. **`connect_readonly()`** opens SQLite with `?mode=ro`. Even if a `DELETE` slipped through everything else, SQLite itself refuses to write. That's safety layer 2.
3. **`is_safe_select(sql)`** (layer 1) accepts only one statement starting with `SELECT` or `WITH`, with no `;` in the middle and none of the words insert/update/delete/drop/alter/attach/pragma/create.
4. **`reviewed(sql, purpose)`** (layer 3) sends the schema, the question and the SQL to the `REVIEWER` agent, which answers with a `Review`: `approved`, `problems`, and a `corrected_sql`. Approved → run it; not approved but fixable → run the safe corrected version and tell the Analyst what changed; otherwise → refuse with the reasons.
5. **`run_sql()`** and **`make_chart()`** both go through `reviewed()` first, so the Analyst has no way to run unreviewed SQL. `run_sql` returns at most 50 rows as a small text table. `make_chart` draws a bar or line chart (2 columns = label/value, 3 columns = one line per series) and saves it under a cleaned-up file name.
6. **`list_tables()`** and **`describe_table()`** let the Analyst explore: column names and 3 sample rows. The table name is checked with a regex before it's put into SQL.
7. **`SCHEMA`** is a short description of the tables, including the business rule "revenue = quantity × price, count only completed orders". Both agents see it; models write much better SQL when they know the columns.
8. **Tests** check the safety filter, that the database refuses writes even when the filter is bypassed, that a reviewer correction is applied before running, and that a chart file gets written.

## If something goes wrong
- **`Run: python make_db.py`** → the database doesn't exist yet. Run `python make_db.py` once in this folder.
- **`anthropic.AuthenticationError`** → set `ANTHROPIC_API_KEY` in this terminal.
- **`sqlite3.OperationalError: no such column ...` in the log** → the Analyst guessed a column name. It sees the error and usually fixes it on the next step; if not, add the column to `SCHEMA`.
- **`ModuleNotFoundError: No module named 'matplotlib'`** → `pip install -r requirements.txt` in your venv.
- **`[Analyst] stopped after 12 steps`** → the question needed more exploring. Raise `max_steps`, or ask a more specific question.

## Try this
1. **Measure accuracy.** Write 5 questions, compute the correct answers yourself in SQL, then check whether the analyst's answer contains your number.
   <details><summary>Solution</summary>

   ```python
   # accuracy.py
   import analyst

   CASES = [("How many completed orders were there in 2026?",
             "SELECT COUNT(*) FROM orders WHERE status='completed'"),
            ("How many customers are from India?",
             "SELECT COUNT(*) FROM customers WHERE country='India'")]
   with analyst.connect_readonly() as con:
       for question, truth_sql in CASES:
           truth = con.execute(truth_sql).fetchone()[0]
           answer = analyst.ANALYST.run(question)
           ok = f"{truth:,}" in answer or str(truth) in answer
           print("✅" if ok else "❌", question, "expected", truth)
   ```
   This is 7.5's eval idea applied to SQL. Try it with and without the reviewer (temporarily make `reviewed()` return `sql, ""` straight away) and compare.
   </details>
2. **A forecast tool.** Add `forecast_next_month()` that fits a straight line to monthly completed revenue (like 3.1's linear regression) and predicts October 2026.
   <details><summary>Solution</summary>

   ```python
   def forecast_next_month() -> str:
       import numpy as np
       with connect_readonly() as con:
           rows = con.execute("""SELECT substr(o.order_date,1,7), SUM(oi.quantity*p.price) FROM orders o
                                 JOIN order_items oi ON oi.order_id=o.id JOIN products p ON p.id=oi.product_id
                                 WHERE o.status='completed' GROUP BY 1 ORDER BY 1""").fetchall()
       y = np.array([r[1] for r in rows]); x = np.arange(len(y))
       slope, intercept = np.polyfit(x, y, 1)                    # best straight line through the points
       return f"Trend {slope:+.0f}/month; next month ≈ {slope * len(y) + intercept:,.0f}"
   ```
   Register it with `Tool("forecast_next_month", "Forecast next month's revenue from the monthly trend", NoArgs, forecast_next_month)` in the Analyst's tool list. This query is fixed code, so it needs no review.
   </details>
3. **A different database.** Point the analyst at the Chinook music-store sample (https://github.com/lerocha/chinook-database, download the SQLite file) and ask "Which genre earns the most?".
   <details><summary>Hint</summary>

   Run with `DB_PATH=Chinook_Sqlite.sqlite python analyst.py "..."` and rewrite `SCHEMA` to describe Chinook's main tables (Invoice, InvoiceLine, Track, Genre...) and its business rules. Without an accurate `SCHEMA`, both agents have to explore with `describe_table` first, which costs more steps.
   </details>

## Check yourself
1. The reviewer exists, so why also open the database read-only?
2. Give an example of a query that runs without errors but gives a wrong business answer.
3. Why is the reviewer called inside `run_sql` instead of being a tool the Analyst can choose to call?
4. Why does putting the schema in the prompt improve the SQL?

<details><summary>Answers</summary>

1. Defence in depth: the reviewer is an AI and can make mistakes or be fooled. The read-only connection is a hard guarantee from the database itself that nothing can be changed.
2. Summing revenue over all orders (including refunded and cancelled ones), or joining orders to order_items and then counting rows as "number of orders" (one order with 3 items counts 3 times).
3. If it were optional, the Analyst could skip it. Inside the tool, review is guaranteed for every query, whatever the Analyst decides.
4. The model doesn't have to guess table and column names or business rules ("count only completed orders"), so it makes fewer mistakes and needs fewer exploring steps.
</details>

## Learn more (optional)
- Text-to-SQL with LLMs, best practices: https://www.youtube.com/results?search_query=text+to+sql+LLM+agent+best+practices
- SQLite URI filenames (read-only mode): https://www.sqlite.org/uri.html
- SQL basics, a free interactive tutorial: https://sqlbolt.com/

## Next
→ [8.5 · Code review crew: parallel reviewers](../05-code-review-crew-parallel-reviewers)
