# discovery_check.py: check your discovery notes for gaps before you write a spec.
#
#   python discovery_check.py northwind_interview_notes.md            (report)
#   python discovery_check.py northwind_interview_notes.md --email    (report + a follow-up email draft)
#
# It reads a notes file made from notes_template.md, finds sections you left empty,
# lists every "TBD", and drafts the follow-up questions for you. No AI needed.
import argparse
import re
import sys
from pathlib import Path

# Every section a good set of discovery notes must have, with the question to ask if it is missing.
REQUIRED = {
    "Who we talked to": "Who else should we talk to, and what are their roles?",
    "The problem in their words": "In your own words, what is the main problem we are solving?",
    "Current process (step by step)": "Could you walk us through the current process step by step?",
    "Pain and impact (numbers)": "Roughly how long does this take today, how often, and what does it cost?",
    "Users and volume": "Who would use the solution day to day, and how many items do they handle per week?",
    "Data sources": "Where does the information for this live, and could we get a sample?",
    "Systems and integrations": "Which systems are involved, and do they have an API or a database we can read?",
    "Security, privacy and compliance": "Which data is sensitive, and where are we allowed to process it?",
    "Success looks like": "How will you judge success in 3 months, and what is the number today?",
    "Constraints (time, budget, people)": "Are there deadlines, budget limits or freezes we should plan around?",
    "Stakeholders and decision makers": "Who decides, who pays, and who needs to approve this?",
    "Risks and unknowns": "What worries you most about this project?",
    "Next steps": "Can we agree owners and dates for the next steps?",
}
EMPTY_MARKERS = {"", "-", "tbd", "todo", "?", "n/a"}


def read_sections(markdown):
    """Split the notes into {heading: [content lines]}. Hint lines (starting with '>') are ignored."""
    sections, current = {}, None
    for raw in markdown.splitlines():
        line = raw.strip()
        if line.startswith("## "):                     # '## ' starts a new section
            current = line[3:].strip()
            sections[current] = []
        elif current and line and not line.startswith(">"):
            sections[current].append(line)
    return sections


def is_answered(lines):
    """A section counts as answered if at least one line has real content (not just 'TBD' or '-')."""
    for line in lines:
        text = re.sub(r"^([-*]|\d+\.)\s*", "", line).strip().lower()   # drop bullet marks like '- ' or '1. '
        if text not in EMPTY_MARKERS:
            return True
    return False


def check(markdown):
    """Return (answered sections, missing sections, open items marked TBD, extra unknown sections)."""
    sections = read_sections(markdown)
    answered = [name for name in REQUIRED if is_answered(sections.get(name, []))]
    missing = [name for name in REQUIRED if name not in answered]
    open_items = [(name, line) for name, lines in sections.items() for line in lines if "TBD" in line]
    extra = [name for name in sections if name not in REQUIRED]
    return answered, missing, open_items, extra


def customer_name(markdown):
    """Take the customer from the title line '# Discovery notes: <customer> · <date>'."""
    match = re.search(r"^# Discovery notes:\s*(.+?)\s*·", markdown, flags=re.MULTILINE)
    return match.group(1) if match else "your team"


def follow_up_email(markdown, missing, open_items):
    """Draft a short, polite follow-up email listing every gap as a question."""
    questions = [REQUIRED[name] for name in missing]
    questions += [re.sub(r"^([-*]|\d+\.)\s*", "", line).replace("TBD", "").strip() for _, line in open_items]
    lines = ["Subject: Thank you, and a few follow-up questions",
             "",
             f"Hi {customer_name(markdown)} team,",
             "",
             "Thank you for your time today. To make sure our design matches how you work, could you help with these:",
             ""]
    lines += [f"{n}. {q}" for n, q in enumerate(questions, start=1)]
    lines += ["", "We will send the draft design doc once we have these. Thanks again!"]
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Find gaps in discovery notes.")
    parser.add_argument("notes", help="path to a notes file made from notes_template.md")
    parser.add_argument("--email", action="store_true", help="also print a follow-up email draft")
    args = parser.parse_args()

    path = Path(args.notes)
    if not path.exists():
        sys.exit(f"Can't find {path}. Check the file name (and that you are in the lesson folder).")
    markdown = path.read_text(encoding="utf-8")
    answered, missing, open_items, extra = check(markdown)

    print(f"Notes: {path.name}")
    print(f"Sections answered: {len(answered)}/{len(REQUIRED)}")
    for name in REQUIRED:
        print(f"  [{'x' if name in answered else ' '}] {name}")
    if extra:
        print("Sections not in the template (check the spelling of the heading): " + ", ".join(extra))
    print(f"Open items (TBD): {len(open_items)}")
    for name, line in open_items:
        print(f"  - {name}: {line}")
    ready = not missing and not open_items
    print("Ready to write the spec!" if ready else "Not ready yet: fill the gaps above (use --email to ask).")
    if args.email and not ready:
        print("\n" + "-" * 60 + "\n" + follow_up_email(markdown, missing, open_items))


if __name__ == "__main__":
    main()
