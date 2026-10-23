# notes_to_spec.py: turn raw discovery notes into a structured problem spec, using an LLM.
#
#   python notes_to_spec.py northwind_interview_notes.md --dry-run     (show what would be sent; no AI, no cost)
#   python notes_to_spec.py northwind_interview_notes.md               (Claude, needs ANTHROPIC_API_KEY)
#   python notes_to_spec.py northwind_interview_notes.md --out spec.md (also save the spec to a file)
#   LLM_PROVIDER=ollama python notes_to_spec.py northwind_interview_notes.md   (a local model, free)
#
# The AI only drafts. YOU check every line against the notes before sending it to the customer.
import argparse
import sys
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field

import llm


class PainPoint(BaseModel):
    pain: str = Field(description="what hurts, in plain words")
    evidence: str = Field(description="the number or quote that proves it, and where it came from")


class Metric(BaseModel):
    name: str = Field(description="what we will measure, e.g. 'median first response time'")
    baseline: Optional[str] = Field(description="the value today, or null if unknown")
    target: Optional[str] = Field(description="the value that means success, or null if unknown")


class ProblemSpec(BaseModel):
    customer: str
    problem_statement: str = Field(description="one sentence: who has what problem, and why it matters")
    requested_solution: str = Field(description="what the customer asked for, in their words")
    real_need: str = Field(description="the outcome they actually need (may differ from what they asked for)")
    users: str = Field(description="who will use it and how many")
    current_process: list[str] = Field(description="today's steps, in order")
    pain_points: list[PainPoint]
    data_sources: list[str]
    systems: list[str]
    constraints: list[str] = Field(description="time, budget, people, security and compliance limits")
    success_metrics: list[Metric]
    open_questions: list[str] = Field(description="everything marked TBD or still unknown")
    risks: list[str]


SYSTEM = ("You are a forward deployed engineer writing a problem spec from discovery notes. "
          "Use ONLY facts written in the notes. Never invent numbers, names or systems. "
          "If something is unknown, put it in open_questions instead of guessing.")


def build_prompt(notes):
    return ("Here are discovery notes from a customer meeting. Turn them into a problem spec.\n\n"
            f"<notes>\n{notes}\n</notes>")


def to_markdown(spec):
    """Render the spec as a short Markdown document you can paste into a design doc."""
    out = [f"# Problem spec: {spec.customer}", "", f"**Problem:** {spec.problem_statement}", "",
           f"**They asked for:** {spec.requested_solution}  ", f"**They need:** {spec.real_need}  ",
           f"**Users:** {spec.users}", "", "## Current process"]
    out += [f"{n}. {step}" for n, step in enumerate(spec.current_process, start=1)]
    out += ["", "## Pain points", "| Pain | Evidence |", "|------|----------|"]
    out += [f"| {p.pain} | {p.evidence} |" for p in spec.pain_points]
    out += ["", "## Success metrics", "| Metric | Baseline | Target |", "|--------|----------|--------|"]
    out += [f"| {m.name} | {m.baseline or 'unknown'} | {m.target or 'unknown'} |" for m in spec.success_metrics]
    for title, items in [("Data sources", spec.data_sources), ("Systems", spec.systems),
                         ("Constraints", spec.constraints), ("Risks", spec.risks),
                         ("Open questions", spec.open_questions)]:
        out += ["", f"## {title}"] + [f"- {item}" for item in items]
    return "\n".join(out) + "\n"


def main():
    parser = argparse.ArgumentParser(description="Draft a problem spec from discovery notes with an LLM.")
    parser.add_argument("notes", help="path to your discovery notes (Markdown)")
    parser.add_argument("--out", help="also save the spec to this file")
    parser.add_argument("--dry-run", action="store_true", help="print the prompt and stop (no AI call)")
    args = parser.parse_args()

    path = Path(args.notes)
    if not path.exists():
        sys.exit(f"Can't find {path}.")
    prompt = build_prompt(path.read_text(encoding="utf-8"))
    if args.dry_run:
        print(f"Would send {len(prompt):,} characters to {llm.PROVIDER} ({llm.model_name()}):\n")
        print(prompt)
        return

    print(f"Asking {llm.PROVIDER} ({llm.model_name()}) to draft the spec...\n", file=sys.stderr)
    spec = llm.ask_json(prompt, ProblemSpec, system=SYSTEM)
    markdown = to_markdown(spec)
    print(markdown)
    if args.out:
        Path(args.out).write_text(markdown, encoding="utf-8")
        print(f"Saved to {args.out}. Now check every line against your notes!", file=sys.stderr)


if __name__ == "__main__":
    main()
