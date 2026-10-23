"""tools.py: each specialist gets its OWN small set of tools (and nothing else). All read-only.

  data_analyst    describe_tables, run_sql                       (the numbers)
  operations      carrier_scorecard, search_ops_notes            (carriers and hubs)
  customer_voice  ticket_stats, sample_tickets                   (what customers say)
  contracts       search_documents, calculate_service_credit     (contracts and policies)
"""
import json
import re
import sqlite3
from pathlib import Path

HERE = Path(__file__).parent
DB = HERE / "northwind.db"
DOCS = HERE / "docs"
MONTH = {"type": "string", "description": "Month as YYYY-MM, e.g. 2026-09", "pattern": r"^\d{4}-\d{2}$"}


def _db() -> sqlite3.Connection:
    if not DB.exists():
        raise FileNotFoundError("northwind.db is missing: run `python make_data.py` first")
    return sqlite3.connect(f"file:{DB}?mode=ro", uri=True)       # read-only: no tool can change the data


def _rows(sql: str, params=()) -> list[dict]:
    with _db() as db:
        cur = db.execute(sql, params)
        cols = [c[0] for c in cur.description]
        return [dict(zip(cols, r)) for r in cur.fetchall()]


# ---------------- data_analyst ----------------
def describe_tables() -> str:
    return ("shipments(id, customer_id, region, hub, carrier, service 'Express'|'Standard', collected_date, "
            "dispatched_date, promised_date, delivered_date, on_time 1|0)  -- dates are 'YYYY-MM-DD' text; "
            "dispatched_date > collected_date means the HUB dispatched late\n"
            "ops_notes(date, carrier, hub, note)\n"
            "tickets(id, created_date, customer_id, category, text)")


def run_sql(query: str) -> str:
    q = query.strip().rstrip(";")
    if not re.match(r"(?is)^\s*(select|with)\b", q) or ";" in q:
        return "ERROR: only a single SELECT (or WITH ... SELECT) query is allowed."
    try:
        rows = _rows(f"SELECT * FROM ({q}) LIMIT 50")
    except sqlite3.Error as e:
        return f"ERROR: {e}. Call describe_tables to check names."
    return json.dumps(rows)


# ---------------- operations ----------------
def carrier_scorecard(month: str) -> str:
    return json.dumps(_rows("""
        SELECT carrier, hub, COUNT(*) AS shipments, ROUND(100.0 * AVG(on_time), 1) AS on_time_pct,
               SUM(dispatched_date > collected_date) AS late_dispatches
        FROM shipments WHERE collected_date LIKE ? GROUP BY carrier, hub ORDER BY on_time_pct""", (f"{month}%",)))


def search_ops_notes(month: str, keyword: str = "") -> str:
    rows = _rows("SELECT date, carrier, hub, note FROM ops_notes WHERE date LIKE ? AND note LIKE ? ORDER BY date",
                 (f"{month}%", f"%{keyword}%"))
    return json.dumps(rows) if rows else "No notes found."


# ---------------- customer_voice ----------------
def ticket_stats(month: str) -> str:
    return json.dumps(_rows("SELECT category, COUNT(*) AS tickets FROM tickets WHERE created_date LIKE ? "
                            "GROUP BY category ORDER BY tickets DESC", (f"{month}%",)))


def sample_tickets(month: str, keyword: str = "", limit: int = 5) -> str:
    total = _rows("SELECT COUNT(*) AS n FROM tickets WHERE created_date LIKE ? AND text LIKE ?",
                  (f"{month}%", f"%{keyword}%"))[0]["n"]
    rows = _rows("SELECT id, created_date, text FROM tickets WHERE created_date LIKE ? AND text LIKE ? LIMIT ?",
                 (f"{month}%", f"%{keyword}%", min(limit, 10)))
    return json.dumps({"matching_tickets": total, "examples": rows})


# ---------------- contracts ----------------
def search_documents(query: str) -> str:
    words = set(re.findall(r"[a-z]{3,}", query.lower()))
    hits = []
    for path in sorted(DOCS.glob("*.md")):
        for section in path.read_text(encoding="utf-8").split("\n## ")[1:]:
            title, _, body = section.partition("\n")
            score = len(words & set(re.findall(r"[a-z]{3,}", (title + body).lower())))
            if score:
                hits.append((score, {"doc": path.name, "section": title, "text": body.strip()}))
    return json.dumps([h for _, h in sorted(hits, key=lambda x: -x[0])[:4]]) if hits else "No matching sections."


def calculate_service_credit(on_time_percent: float, invoice_gbp: float) -> str:
    """Code does contract maths, not the model: 5% of the invoice per full point below 95%, capped at 25%."""
    points = max(0, int(95 - on_time_percent))
    rate = min(0.05 * points, 0.25)
    return json.dumps({"points_below_95": points, "credit_rate": rate, "credit_gbp": round(invoice_gbp * rate, 2)})


def _tool(fn, description, properties, required):
    return {"name": fn.__name__, "description": description,
            "input_schema": {"type": "object", "properties": properties, "required": required}}, fn


TOOLSETS = {
    "data_analyst": [
        _tool(describe_tables, "Show the tables and columns you can query. Use this before writing SQL.", {}, []),
        _tool(run_sql, "Run ONE read-only SQLite SELECT on the shipments, ops_notes and tickets tables (max 50 rows back). "
              "Aggregate with GROUP BY instead of fetching raw rows.",
              {"query": {"type": "string", "description": "A single SELECT statement"}}, ["query"]),
    ],
    "operations": [
        _tool(carrier_scorecard, "On-time % and late hub dispatches per carrier and hub for one month.",
              {"month": MONTH}, ["month"]),
        _tool(search_ops_notes, "Read operations notes (carrier calls, hub incidents) for one month, optionally by keyword.",
              {"month": MONTH, "keyword": {"type": "string", "description": "Optional word to filter on, e.g. 'Leeds'"}},
              ["month"]),
    ],
    "customer_voice": [
        _tool(ticket_stats, "Count support tickets by category for one month.", {"month": MONTH}, ["month"]),
        _tool(sample_tickets, "How many tickets in a month mention a keyword, plus up to 10 examples.",
              {"month": MONTH, "keyword": {"type": "string", "description": "Word to look for, e.g. 'tracking'"},
               "limit": {"type": "integer", "description": "Examples to return (1-10)", "minimum": 1, "maximum": 10}},
              ["month"]),
    ],
    "contracts": [
        _tool(search_documents, "Search Northwind's carrier contracts, customer policies and project plans.",
              {"query": {"type": "string", "description": "Words to look for, e.g. 'SwiftHaul service credit'"}}, ["query"]),
        _tool(calculate_service_credit, "Compute a carrier's SLA service credit exactly (never do this maths yourself).",
              {"on_time_percent": {"type": "number", "description": "The month's on-time %, e.g. 87.5"},
               "invoice_gbp": {"type": "number", "description": "That month's carrier invoice in GBP"}},
              ["on_time_percent", "invoice_gbp"]),
    ],
}
