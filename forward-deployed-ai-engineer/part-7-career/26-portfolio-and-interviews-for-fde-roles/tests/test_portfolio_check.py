import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from portfolio_check import check  # noqa: E402


def test_empty_project_scores_low(tmp_path):
    (tmp_path / "README.md").write_text("# my project\n")
    score, rows = check(tmp_path)
    assert score == 5                                           # only "no secrets committed"


def test_good_project_scores_full(tmp_path):
    (tmp_path / "README.md").write_text(
        "# Claims desk\n## Why this matters\nFor claims handlers.\n```bash\npytest -q\n```\n```mermaid\nflowchart LR\n```\n"
        "### What you should see\nEval pass rate 100 %.\nTrade-offs: rules as code instead of the model.\n")
    (tmp_path / "test_app.py").write_text("def test_x(): pass\n")
    (tmp_path / "Dockerfile").write_text("FROM python:3.12-slim\n")
    (tmp_path / "requirements.txt").write_text("fastapi==0.143.0\n")
    assert check(tmp_path)[0] == 100


def test_committed_key_is_caught(tmp_path):
    (tmp_path / "README.md").write_text("# x\n")
    (tmp_path / "config.py").write_text('KEY = "sk-ant-' + "a" * 30 + '"\n')
    rows = check(tmp_path)[1]
    assert not rows[-1][0]
