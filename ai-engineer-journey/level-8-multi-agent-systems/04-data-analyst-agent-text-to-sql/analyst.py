"""Project 8.4: ask business questions in plain English; an Analyst agent writes SQL, a Reviewer agent checks every
query BEFORE it runs, and results come back as answers and charts.

python make_db.py && python analyst.py "Which product category made the most revenue per month this year? Make a chart."
"""
import os
import re
import sqlite3
import sys

from pydantic import BaseModel, Field

from agent_core import Agent, Tool, cost_report

DB_PATH = os.getenv("DB_PATH", "shop.db")


def connect_readonly():
    # mode=ro: even if an agent writes "DROP TABLE", SQLite itself refuses. Defence in depth!
    return sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)


# ---------------- Tools ----------------
class NoArgs(BaseModel):
    pass


class TableName(BaseModel):
    table: str


class SqlIn(BaseModel):
    sql: str = Field(description="ONE SQLite SELECT statement")
    purpose: str = Field(description="What question this query answers")


class ChartIn(BaseModel):
    sql: str = Field(description="SELECT returning exactly 2 columns (label, value) or 3 columns (x, series, value)")
    title: str
    kind: str = Field(description="'bar' or 'line'")
    filename: str = Field(description="e.g. revenue_by_month.png")


def list_tables() -> str:
    with connect_readonly() as con:
        return ", ".join(r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'"))


def describe_table(table: str) -> str:
    if not re.fullmatch(r"[A-Za-z_]+", table):
        return "Invalid table name"
    with connect_readonly() as con:
        cols = con.execute(f"PRAGMA table_info({table})").fetchall()
        sample = con.execute(f"SELECT * FROM {table} LIMIT 3").fetchall()
    return f"columns: {[(c[1], c[2]) for c in cols]}\nsample rows: {sample}"


def is_safe_select(sql: str) -> bool:
    s = sql.strip().rstrip(";").lower()
    return s.startswith(("select", "with")) and ";" not in s and not re.search(r"\b(insert|update|delete|drop|alter|attach|pragma|create)\b", s)


REVIEWER = None   # set below; the run_sql tool consults it


class Review(BaseModel):
    approved: bool
    problems: list[str] = Field(description="Bugs: wrong joins, double counting, wrong filters, missing status filter, etc.")
    corrected_sql: str | None = Field(description="A fixed query if not approved, else null")


def run_sql(sql: str, purpose: str, max_rows: int = 50) -> str:
    if not is_safe_select(sql):
        return "REJECTED: only a single read-only SELECT is allowed."
    review = REVIEWER.ask_structured(f"Schema:\n{SCHEMA}\n\nQuestion: {purpose}\n\nSQL:\n{sql}", Review)
    if not review.approved:
        if review.corrected_sql and is_safe_select(review.corrected_sql):
            sql = review.corrected_sql
        else:
            return f"Reviewer rejected the query: {review.problems}"
    with connect_readonly() as con:
        cur = con.execute(sql)
        cols = [d[0] for d in cur.description]
        rows = cur.fetchmany(max_rows)
    note = "" if review.approved else f"(Reviewer fixed the query: {review.problems})\n"
    return note + " | ".join(cols) + "\n" + "\n".join(" | ".join(str(v) for v in r) for r in rows)


def make_chart(sql: str, title: str, kind: str, filename: str) -> str:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    if not is_safe_select(sql):
        return "REJECTED: only SELECT is allowed."
    with connect_readonly() as con:
        rows = con.execute(sql).fetchall()
    fig, ax = plt.subplots(figsize=(9, 4.5))
    if rows and len(rows[0]) == 3:                         # x, series, value -> one line/bar group per series
        for series in sorted({r[1] for r in rows}):
            pts = [(r[0], r[2]) for r in rows if r[1] == series]
            (ax.plot if kind == "line" else ax.bar)([p[0] for p in pts], [p[1] for p in pts], label=str(series))
        ax.legend()
    else:
        (ax.plot if kind == "line" else ax.bar)([str(r[0]) for r in rows], [r[1] for r in rows])
    ax.set_title(title); plt.xticks(rotation=45, ha="right"); plt.tight_layout()
    name = re.sub(r"[^\w.-]", "_", filename)
    fig.savefig(name, dpi=110); plt.close(fig)
    return f"Saved chart to {name}"


SCHEMA = """customers(id, name, country, signup_date)
products(id, name, category, price)
orders(id, customer_id, order_date 'YYYY-MM-DD', status in completed/refunded/cancelled)
order_items(order_id, product_id, quantity)   revenue = quantity * products.price, count only completed orders"""

REVIEWER = Agent("SQL-Reviewer", "You are a senior data engineer reviewing SQL for correctness. Approve correct queries; "
                                 "fix wrong ones. Watch for double counting from joins and for missing status = 'completed' filters.",
                 effort="low")
ANALYST = Agent("Analyst", ("You are a data analyst for an online shop. Explore the schema with tools, query with run_sql, "
                            "and answer with concrete numbers. Make a chart with make_chart when trends or comparisons are asked for. "
                            f"Known schema:\n{SCHEMA}"),
                tools=[Tool("list_tables", "List tables", NoArgs, list_tables),
                       Tool("describe_table", "Columns and sample rows of a table", TableName, describe_table),
                       Tool("run_sql", "Run a read-only SELECT (reviewed before execution)", SqlIn, run_sql),
                       Tool("make_chart", "Create a PNG chart from a SELECT", ChartIn, make_chart)],
                max_steps=12)

if __name__ == "__main__":
    if not os.path.exists(DB_PATH):
        sys.exit("Run: python make_db.py")
    questions = sys.argv[1:] or ["What were total revenue and number of completed orders per month in 2026? Chart it.",
                                 "Which 3 countries bring the most revenue, and what's their average order value?",
                                 "Which product has the highest refund rate?"]
    for q in questions:
        print("\n" + "=" * 70 + f"\n❓ {q}\n")
        print(ANALYST.run(q))
    print("\n" + cost_report([ANALYST, REVIEWER]))
