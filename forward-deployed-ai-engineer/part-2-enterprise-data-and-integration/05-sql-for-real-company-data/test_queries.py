import os
import sqlite3
from pathlib import Path

import pytest

import make_db
import run_sql

HERE = Path(__file__).parent
PORTABLE = sorted((HERE / "queries").glob("0[1-7]_*.sql"))     # files 01-07 run on SQLite and PostgreSQL


@pytest.fixture(scope="module")
def db(tmp_path_factory):
    path = tmp_path_factory.mktemp("data") / "northwind.db"
    make_db.main(path)
    return path


def query(db, sql):
    return sqlite3.connect(db).execute(sql).fetchall()


def test_build_is_identical_every_time(db, tmp_path):
    second = tmp_path / "again.db"
    make_db.main(second)
    for table in ["customers", "shipments", "scans", "tickets", "invoices"]:
        assert query(db, f"SELECT * FROM {table} ORDER BY 1") == query(second, f"SELECT * FROM {table} ORDER BY 1")


def test_messiness_is_there_on_purpose(db):
    spellings = query(db, "SELECT COUNT(DISTINCT category) FROM tickets")[0][0]
    assert spellings == 16
    assert query(db, "SELECT COUNT(*) FROM tickets WHERE category IS NULL")[0][0] > 0


@pytest.mark.parametrize("path", PORTABLE, ids=lambda p: p.name)
def test_every_portable_query_runs(db, path):
    con = sqlite3.connect(db)
    statements = run_sql.split_statements(path.read_text())
    assert statements, "file has no queries"
    for statement in statements:
        columns, rows = run_sql.run(con, statement)
        assert columns and rows, f"no result for: {run_sql.title_of(statement)}"


def test_wismo_share_confirms_discovery(db):
    sql = (HERE / "queries" / "05_ctes.sql").read_text()
    first = run_sql.split_statements(sql)[0]
    rows = dict((cat, pct) for cat, _, pct in run_sql.run(sqlite3.connect(db), first)[1])
    assert rows["wismo"] == pytest.approx(41.2)


def test_median_response_time_matches_discovery(db):
    sql = (HERE / "queries" / "08_response_times.sql").read_text()
    medians = dict((cat, h) for cat, _, h in run_sql.run(sqlite3.connect(db), run_sql.split_statements(sql)[0])[1])
    assert 15 < medians["wismo"] < 22                              # about 19 hours, as Priya's report said


def test_split_keeps_semicolons_inside_strings():
    sql = "-- one\nSELECT 'a;b' AS x;\n-- two\nSELECT 2;\n-- only a comment\n"
    statements = run_sql.split_statements(sql)
    assert len(statements) == 2 and run_sql.title_of(statements[1]) == "two"


def test_connection_is_read_only(db, monkeypatch):
    monkeypatch.setattr(run_sql, "DB", db)
    con = run_sql.connect()
    with pytest.raises(sqlite3.OperationalError, match="readonly"):
        con.execute("DELETE FROM tickets")


def test_table_formatting_shows_nulls_and_limits():
    text = run_sql.as_table(["a"], [(None,)] * 25, limit=3)
    assert "NULL" in text and "... (22 more rows)" in text and "(25 rows)" in text


@pytest.mark.skipif(not os.getenv("NORTHWIND_PG_URL"), reason="set NORTHWIND_PG_URL to test PostgreSQL")
def test_same_answers_on_postgres(db):
    import psycopg
    pg = psycopg.connect(os.environ["NORTHWIND_PG_URL"], autocommit=True)
    for path in PORTABLE:
        for statement in run_sql.split_statements(path.read_text()):
            lite = run_sql.run(sqlite3.connect(db), statement)[1]
            post = run_sql.run(pg, statement)[1]
            assert [tuple(map(str, map(float_or_same, r))) for r in lite] == \
                   [tuple(map(str, map(float_or_same, r))) for r in post], run_sql.title_of(statement)


def float_or_same(value):
    try:
        return float(value)                                         # 146370.0 (SQLite) == Decimal('146370') (PG)
    except (TypeError, ValueError):
        return value
