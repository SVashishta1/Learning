# run_sql.py: run SQL against northwind.db (read-only) and print neat tables.
#
#   python run_sql.py queries/01_first_look.sql                      (every query in a file)
#   python run_sql.py -e "SELECT COUNT(*) FROM tickets"               (one query typed here)
#   python run_sql.py queries/05_ctes.sql --postgres postgresql://localhost/northwind   (same SQL on Postgres)
#
# The database is opened READ-ONLY. When you query a customer's database, you never want a typo to change it.
import argparse
import re
import sqlite3
import sys
from pathlib import Path

DB = Path(__file__).parent / "northwind.db"
MAX_ROWS = 20                                   # print at most this many rows per query


def split_statements(sql):
    """Split a file into single statements. Comment lines (starting with --) are kept with their query."""
    statements, current = [], ""
    for line in sql.splitlines(keepends=True):
        current += line
        if sqlite3.complete_statement(current):  # True once `current` ends with a full statement and ';'
            if re.sub(r"--[^\n]*", "", current).strip(" \n;"):    # skip pieces that are only comments
                statements.append(current.strip())
            current = ""
    if re.sub(r"--[^\n]*", "", current).strip():
        statements.append(current.strip())        # a last statement without ';'
    return statements


def connect(postgres_url=None):
    if postgres_url:
        import psycopg                            # only needed for --postgres
        return psycopg.connect(postgres_url, autocommit=True)
    if not DB.exists():
        sys.exit("northwind.db not found. Run: python make_db.py")
    return sqlite3.connect(f"file:{DB}?mode=ro", uri=True)       # mode=ro: read-only


def run(con, statement):
    """Run one statement and return (column names, rows)."""
    cursor = con.cursor()
    cursor.execute(statement)
    if cursor.description is None:               # statements like PRAGMA may return nothing
        return [], []
    columns = [d[0] for d in cursor.description]
    return columns, cursor.fetchall()


def as_table(columns, rows, limit=MAX_ROWS):
    """Format rows as a plain-text table with a header line."""
    shown = [["NULL" if v is None else str(v) for v in row] for row in rows[:limit]]
    widths = [max([len(c)] + [len(r[i]) for r in shown]) for i, c in enumerate(columns)]
    line = lambda cells: " | ".join(cell.ljust(w) for cell, w in zip(cells, widths))
    out = [line(columns), "-+-".join("-" * w for w in widths)] + [line(r) for r in shown]
    if len(rows) > limit:
        out.append(f"... ({len(rows) - limit} more rows)")
    out.append(f"({len(rows)} row{'s' if len(rows) != 1 else ''})")
    return "\n".join(out)


def title_of(statement):
    """The '-- ...' comment line just above a query is its title (file headers above it are skipped)."""
    title = None
    for line in statement.splitlines():
        stripped = line.strip()
        if stripped.startswith("--"):
            title = stripped[2:].strip()
        elif stripped:                            # the first real SQL line: stop looking
            break
    return title


def main():
    parser = argparse.ArgumentParser(description="Run SQL against northwind.db (read-only).")
    parser.add_argument("file", nargs="?", help="a .sql file with one or more queries")
    parser.add_argument("-e", "--execute", help="a single SQL query to run")
    parser.add_argument("--postgres", metavar="URL", help="run on PostgreSQL instead of SQLite")
    args = parser.parse_args()
    if not args.file and not args.execute:
        parser.error("give a .sql file or -e \"SELECT ...\"")

    sql = args.execute if args.execute else Path(args.file).read_text(encoding="utf-8")
    con = connect(args.postgres)
    for statement in split_statements(sql):
        title = title_of(statement)
        if title:
            print(f"\n== {title}")
        try:
            columns, rows = run(con, statement)
        except Exception as error:                # show the database's message, then carry on
            print(f"ERROR: {error}")
            continue
        if columns:
            print(as_table(columns, rows))
    con.close()


if __name__ == "__main__":
    main()
