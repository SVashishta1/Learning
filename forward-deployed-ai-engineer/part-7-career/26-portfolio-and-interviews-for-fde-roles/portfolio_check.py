"""portfolio_check.py: is a project folder ready to show a hiring manager? Prints a score and what to fix.

    python portfolio_check.py ../../part-6-impact-capstones/23-capstone-disaster-relief-command-center
    python portfolio_check.py ~/code/my-project --min 80     # exit code 1 below 80 (use it in CI)

It reads the README and the folder. It can't judge quality, only whether a reviewer can find the basics in 2 minutes.
"""
import argparse
import re
import sys
from pathlib import Path

# (points, what a reviewer looks for, how we detect it in the README text or the folder)
CHECKS = [
    (15, "says what problem it solves, for whom", lambda r, f: re.search(r"why (this|it) matters|problem|for whom|users?", r, re.I)),
    (10, "shows how to run it in a few commands", lambda r, f: re.search(r"```(bash|sh|shell)", r)),
    (10, "has a diagram of how it works", lambda r, f: "```mermaid" in r or re.search(r"!\[.*\]\(.*\.(png|svg|gif)\)", r)),
    (10, "shows real output, a screenshot or a demo link", lambda r, f: re.search(r"what you should see|demo|screenshot|example output|\.gif", r, re.I)),
    (15, "has automated tests", lambda r, f: any(f.rglob("test_*.py")) or any(f.rglob("*.test.*"))),
    (15, "measures quality (evals, metrics, results)", lambda r, f: re.search(r"\beval|golden|accuracy|pass rate|metric|results?\b", r, re.I)),
    (10, "explains trade-offs or design decisions", lambda r, f: re.search(r"trade-?off|decision|alternative|why not|instead of", r, re.I)),
    (5, "can be deployed (Dockerfile / compose / manifests)", lambda r, f: any(f.glob("Dockerfile")) or any(f.glob("compose.y*ml"))
                                                                           or any(f.glob("docker-compose.y*ml"))),
    (5, "pins its dependencies", lambda r, f: (f / "requirements.txt").exists() and "==" in (f / "requirements.txt").read_text()
                                              or (f / "pyproject.toml").exists() or (f / "package-lock.json").exists()),
    (5, "keeps secrets out of the code (no API keys committed)", lambda r, f: not any(
        re.search(r"sk-ant-[A-Za-z0-9_-]{20,}|AKIA[0-9A-Z]{16}", p.read_text(errors="ignore"))
        for p in f.rglob("*") if p.is_file() and p.suffix in {".py", ".md", ".yaml", ".yml", ".json", ".env", ".txt"})),
]


def check(folder: Path) -> tuple[int, list[tuple[bool, int, str]]]:
    readme = next((p for p in (folder / "README.md", folder / "readme.md") if p.exists()), None)
    text = readme.read_text(encoding="utf-8", errors="ignore") if readme else ""
    rows = [(bool(test(text, folder)), points, label) for points, label, test in CHECKS]
    return sum(points for ok, points, _ in rows if ok), rows


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Portfolio-readiness check for a project folder")
    ap.add_argument("folder", type=Path)
    ap.add_argument("--min", type=int, default=0, help="exit with code 1 if the score is lower")
    args = ap.parse_args()
    if not args.folder.is_dir():
        sys.exit(f"Not a folder: {args.folder}")
    score, rows = check(args.folder)
    print(f"Portfolio check: {args.folder.resolve().name}")
    for ok, points, label in rows:
        print(f"  {'✅' if ok else '❌'} {points:>2} pts  {label}")
    print(f"Score: {score}/100" + ("  (add the ❌ items before you share it)" if score < 100 else ""))
    sys.exit(1 if score < args.min else 0)
