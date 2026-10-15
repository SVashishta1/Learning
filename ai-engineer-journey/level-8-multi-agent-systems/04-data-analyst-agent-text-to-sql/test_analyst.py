import os
import tempfile

os.environ["DB_PATH"] = os.path.join(tempfile.mkdtemp(), "test.db")
import analyst  # noqa: E402
import make_db  # noqa: E402
from fake_llm import FakeClient  # noqa: E402

make_db.build(os.environ["DB_PATH"])
analyst.REVIEWER.verbose = False


def test_safety_filter():
    assert analyst.is_safe_select("SELECT * FROM orders")
    assert analyst.run_sql("DROP TABLE orders", "oops").startswith("REJECTED")
    assert not analyst.is_safe_select("DROP TABLE orders")
    assert not analyst.is_safe_select("SELECT 1; DELETE FROM orders")


def test_database_is_read_only_even_if_filter_is_bypassed():
    import sqlite3
    import pytest
    with pytest.raises(sqlite3.OperationalError):
        analyst.connect_readonly().execute("DELETE FROM orders")


def test_reviewer_can_fix_a_query_before_it_runs():
    analyst.REVIEWER.client = FakeClient(parsed=[analyst.Review(
        approved=False, problems=["missing status filter"],
        corrected_sql="SELECT COUNT(*) AS n FROM orders WHERE status = 'completed'")])
    out = analyst.run_sql("SELECT COUNT(*) AS n FROM orders", "how many completed orders?")
    assert "Reviewer fixed" in out and "n" in out
    assert int(out.strip().splitlines()[-1]) < 2000


def test_chart_is_written(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    analyst.REVIEWER.client = FakeClient(parsed=[analyst.Review(approved=True, problems=[], corrected_sql=None)])
    msg = analyst.make_chart("SELECT category, COUNT(*) FROM products GROUP BY category", "Products", "bar", "p.png")
    assert (tmp_path / "p.png").exists() and "Saved" in msg
