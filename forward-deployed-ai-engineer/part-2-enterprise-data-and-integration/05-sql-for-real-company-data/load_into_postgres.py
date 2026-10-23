# load_into_postgres.py: copy northwind.db (SQLite) into a PostgreSQL database, so you can run the same queries there.
#
#   python load_into_postgres.py postgresql://localhost/northwind
#
# The database in the URL must already exist (createdb northwind). Tables are dropped and re-created each run.
# Many customers run PostgreSQL, so it's worth seeing the same SQL work on both.
import sqlite3
import sys
from pathlib import Path

import psycopg

from make_db import SCHEMA

DB = Path(__file__).parent / "northwind.db"
TABLES = ["customers", "shipments", "scans", "tickets", "invoices"]   # parents before children (foreign keys)


def postgres_schema():
    """Same tables, PostgreSQL types: exact NUMERIC for money and weights instead of SQLite's REAL."""
    return SCHEMA.replace(" REAL", " NUMERIC(12, 2)")


def main():
    if len(sys.argv) != 2:
        sys.exit("Usage: python load_into_postgres.py postgresql://USER@HOST/DATABASE")
    if not DB.exists():
        sys.exit("northwind.db not found. Run: python make_db.py")
    source = sqlite3.connect(DB)
    with psycopg.connect(sys.argv[1]) as target:              # 'with' commits at the end, or rolls back on error
        with target.cursor() as cur:
            cur.execute("DROP TABLE IF EXISTS " + ", ".join(reversed(TABLES)))
            cur.execute(postgres_schema())
            for table in TABLES:
                rows = source.execute(f"SELECT * FROM {table}").fetchall()
                with cur.copy(f"COPY {table} FROM STDIN") as copy:   # COPY is PostgreSQL's fast bulk loader
                    for row in rows:
                        copy.write_row(row)
                print(f"  {table:<10} {len(rows):>6,} rows copied")
    print("Done. Try: python run_sql.py queries/05_ctes.sql --postgres " + sys.argv[1])


if __name__ == "__main__":
    main()
