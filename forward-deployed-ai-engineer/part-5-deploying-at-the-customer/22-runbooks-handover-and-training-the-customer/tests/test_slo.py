import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import make_sample_log  # noqa: E402
import slo_report  # noqa: E402


def rows(statuses, latency=1000, hour=10):
    return [{"ts": f"2026-09-01T{hour:02d}:{i % 60:02d}:00", "status": s, "latency_ms": latency, "route": "/draft"}
            for i, s in enumerate(statuses)]


def test_availability_and_budget():
    r = slo_report.report(rows([200] * 995 + [503] * 5), availability_slo=99.5)
    assert round(r["availability"], 2) == 99.5 and round(r["budget_used_pct"]) == 100


def test_client_errors_do_not_count_against_us():
    assert slo_report.report(rows([200] * 90 + [404] * 10))["availability"] == 100.0


def test_burn_rate_pages_only_on_busy_bad_hours():
    busy_bad = rows([200] * 80 + [500] * 20, hour=10)               # 20 % errors = 40x burn at a 99.5 % SLO
    quiet = rows([500] * 2, hour=3)                                   # 2 errors at night, too few requests to page
    pages = slo_report.report(busy_bad + quiet)["pages"]
    assert pages == ["2026-09-01T10:00 burn rate 40x"]


def test_percentiles():
    assert slo_report.percentile([1, 2, 3, 4, 5, 6, 7, 8, 9, 10], 95) == 10
    assert slo_report.percentile([1, 2, 3, 4], 50) == 2


def test_sample_log_shows_the_planted_incidents(tmp_path):
    path = tmp_path / "requests.jsonl"
    make_sample_log.main(path)
    r = slo_report.report(slo_report.load(str(path)))
    assert r["worst_days"][0][0] == "2026-09-18" and r["availability"] < 99.5
    assert any(d == "2026-09-25" for d, *_ in r["worst_days"])         # the slow-prompt day
    assert all(p.startswith("2026-09-18") for p in r["pages"])
