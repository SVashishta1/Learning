# lint_design_doc.py: a spell-checker for design docs. It catches the mistakes reviewers always find:
# missing sections, metrics without numbers, no non-goals, risks without an owner, and vague words.
#
#   python lint_design_doc.py northwind_design_doc.md
#
# Exit code 0 = no errors (warnings are OK), 1 = errors. So it can run in CI (cloud-and-devops-for-ai, lesson 04).
import re
import sys
from pathlib import Path

REQUIRED = ["Summary", "Background and problem", "Goals", "Non-goals", "Success metrics",
            "Users and use cases", "Proposed solution", "Data and integrations",
            "Security, privacy and compliance", "Evaluation plan", "Rollout plan", "Risks",
            "Open questions", "Alternatives considered", "Sign-off"]
# Words that sound good but can't be measured. Fine in prose, a warning in Goals and Success metrics.
VAGUE = ["better", "faster", "improve", "seamless", "robust", "easy", "efficient", "user-friendly",
         "scalable", "best-in-class", "world-class", "significantly"]


def sections(markdown):
    """{heading: [lines]} for every '## ' heading. Hint lines ('>') are dropped."""
    result, current = {}, None
    for raw in markdown.splitlines():
        line = raw.strip()
        if line.startswith("## "):
            current = line[3:].strip()
            result[current] = []
        elif current and line and not line.startswith(">"):
            result[current].append(line)
    return result


def table_rows(lines):
    """Turn Markdown table lines into lists of cells, skipping the header and the |---| line."""
    rows = [[cell.strip() for cell in line.strip("|").split("|")] for line in lines if line.startswith("|")]
    return [row for row in rows[1:] if not all(set(cell) <= set("-: ") for cell in row)]


def lint(markdown):
    """Return (errors, warnings): two lists of plain-English problems."""
    errors, warnings = [], []
    found = sections(markdown)

    for name in REQUIRED:
        if name not in found:
            errors.append(f"Missing section: '## {name}'")
        elif not found[name]:
            errors.append(f"Empty section: '## {name}'")

    metrics = table_rows(found.get("Success metrics", []))
    if "Success metrics" in found and not metrics:
        errors.append("Success metrics: add a table with at least one metric")
    primaries = [row for row in metrics if len(row) > 1 and row[1].lower() == "primary"]
    if metrics and len(primaries) != 1:
        errors.append("Success metrics: mark exactly one metric as 'primary' in the Type column")
    for row in metrics:
        name = row[0]
        if len(row) < 5:
            errors.append(f"Success metrics: '{name}' needs Type, Baseline, Target and How we measure")
            continue
        if row[2] in {"", "<today's number>"}:
            errors.append(f"Success metrics: '{name}' has no baseline (write 'not measured' if unknown)")
        if not re.search(r"\d", row[3]):
            errors.append(f"Success metrics: '{name}' target has no number")
        if not row[4] or row[4].startswith("<"):
            errors.append(f"Success metrics: '{name}' doesn't say how it is measured")

    bullets = [line for line in found.get("Non-goals", []) if line.startswith(("-", "*"))]
    if "Non-goals" in found and len(bullets) < 3:
        warnings.append(f"Non-goals: only {len(bullets)} listed; aim for at least 3")

    for row in table_rows(found.get("Risks", [])):
        if len(row) < 5 or not row[3] or row[3].startswith("<"):
            errors.append(f"Risks: '{row[0]}' has no mitigation")
        elif not row[4] or row[4].startswith("<"):
            errors.append(f"Risks: '{row[0]}' has no owner")

    for name in ("Goals", "Success metrics"):
        text = " ".join(found.get(name, [])).lower()
        for word in VAGUE:
            if re.search(rf"\b{re.escape(word)}\b", text):
                warnings.append(f"{name}: vague word '{word}'. Say by how much, from what to what")
    return errors, warnings


def main():
    if len(sys.argv) != 2:
        sys.exit("Usage: python lint_design_doc.py <design_doc.md>")
    path = Path(sys.argv[1])
    if not path.exists():
        sys.exit(f"Can't find {path}.")
    errors, warnings = lint(path.read_text(encoding="utf-8"))
    for problem in errors:
        print(f"ERROR   {problem}")
    for problem in warnings:
        print(f"WARNING {problem}")
    print(f"\n{path.name}: {len(errors)} error(s), {len(warnings)} warning(s)")
    sys.exit(1 if errors else 0)                    # a non-zero exit code tells scripts and CI "this failed"


if __name__ == "__main__":
    main()
