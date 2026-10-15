"""Project 8.5: a code-review CREW. Three specialist reviewers read the code IN PARALLEL, then a lead
merges, de-duplicates and ranks their findings into one report.

python review_crew.py sample_code/user_service.py
python review_crew.py --diff            # review your uncommitted git changes instead
"""
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field

from agent_core import Agent, cost_report


class Finding(BaseModel):
    line: int | None = Field(description="Line number in the numbered code, if applicable")
    severity: Literal["critical", "high", "medium", "low"]
    title: str
    why_it_matters: str
    fix: str = Field(description="Concrete fix, with a short code snippet if useful")


class Findings(BaseModel):
    findings: list[Finding]


class FinalReport(BaseModel):
    summary: str = Field(description="2-3 sentence overall assessment")
    merge_recommendation: Literal["approve", "approve_with_changes", "request_changes"]
    findings: list[Finding] = Field(description="Merged, de-duplicated, most severe first")


FOCUS = {
    "Security": "security vulnerabilities: injection (SQL, command), unsafe deserialization, hardcoded secrets, path traversal, missing input validation",
    "Correctness": "bugs: crashes on edge cases (empty input, None, division by zero), swallowed exceptions, wrong logic, off-by-one errors",
    "Maintainability": "readability, naming, performance (e.g. O(n²) loops), missing tests, missing type hints and docstrings",
}


def numbered(code: str) -> str:
    return "\n".join(f"{i:4d} | {line}" for i, line in enumerate(code.splitlines(), start=1))


def review(code: str, client=None, verbose=True) -> tuple[FinalReport, list[Agent]]:
    reviewers = [Agent(f"{area}-Reviewer", f"You are a senior engineer reviewing ONLY for {focus}. Report real issues, not nitpicks outside your area.",
                       client=client, verbose=verbose, effort="medium") for area, focus in FOCUS.items()]
    prompt = f"Review this code:\n\n{numbered(code)}"
    with ThreadPoolExecutor(max_workers=len(reviewers)) as pool:
        partials = list(pool.map(lambda r: r.ask_structured(prompt, Findings), reviewers))

    lead = Agent("Lead-Reviewer", ("You are the tech lead. Merge the reviewers' findings: remove duplicates, keep the clearest "
                                   "explanation, fix severities if they're off, order by severity, and decide whether to merge."),
                 client=client, verbose=verbose, effort="medium")
    collected = "\n".join(f"[{r.name}] {f.model_dump_json()}" for r, p in zip(reviewers, partials) for f in p.findings)
    final = lead.ask_structured(f"Code:\n{numbered(code)}\n\nReviewer findings:\n{collected}", FinalReport)
    return final, [*reviewers, lead]


def to_markdown(report: FinalReport, name: str) -> str:
    icon = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🔵"}
    lines = [f"# Code review: {name}", "", f"**Recommendation:** `{report.merge_recommendation}`", "", report.summary, "",
             "| # | Severity | Line | Issue |", "|---|----------|------|-------|"]
    lines += [f"| {i} | {icon[f.severity]} {f.severity} | {f.line or '-'} | {f.title} |" for i, f in enumerate(report.findings, 1)]
    for i, f in enumerate(report.findings, 1):
        lines += ["", f"### {i}. {f.title}", f"*Why it matters:* {f.why_it_matters}", "", f"*Fix:* {f.fix}"]
    return "\n".join(lines)


if __name__ == "__main__":
    if "--diff" in sys.argv:
        code, name = subprocess.run(["git", "diff"], capture_output=True, text=True).stdout, "git diff"
    else:
        path = Path(sys.argv[1] if len(sys.argv) > 1 else "sample_code/user_service.py")
        code, name = path.read_text(encoding="utf-8"), path.name
    if not code.strip():
        sys.exit("Nothing to review.")
    report, agents = review(code)
    md = to_markdown(report, name)
    Path("review.md").write_text(md, encoding="utf-8")
    print("\n" + md + "\n\nSaved review.md\n")
    print(cost_report(agents))
