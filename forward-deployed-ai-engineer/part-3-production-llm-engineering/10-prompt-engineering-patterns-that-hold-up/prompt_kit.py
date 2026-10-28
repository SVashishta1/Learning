"""prompt_kit.py: prompts live in files, have version numbers, and are locked by a fingerprint.

python prompt_kit.py           # list every prompt, its version, fingerprint and lock status
python prompt_kit.py --lock    # after you change a prompt AND bump its version: record the new fingerprints
"""
import hashlib
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path

PROMPTS = Path(__file__).with_name("prompts")
LOCK_FILE = Path(__file__).with_name("prompts.lock.json")
PLACEHOLDER = re.compile(r"\{\{(\w+)\}\}")           # {{ticket}} -> "ticket"


@dataclass
class Prompt:
    name: str
    version: int
    meta: dict            # everything in the --- header: owner, changed, changelog ...
    system: str           # the part above "=== user ===": stable rules, sent as the system prompt
    user_template: str    # the part below: has {{placeholders}} for this request's data
    path: Path

    @property
    def fingerprint(self) -> str:
        """12 characters that change whenever ANY character of the prompt changes."""
        return hashlib.sha256((self.system + "\n" + self.user_template).encode()).hexdigest()[:12]

    def render_user(self, **values) -> str:
        needed = set(PLACEHOLDER.findall(self.user_template))
        if needed != set(values):
            raise ValueError(f"{self.path.name} needs {sorted(needed)}, got {sorted(values)}")
        return PLACEHOLDER.sub(lambda m: escape(str(values[m.group(1)])), self.user_template)


def escape(text: str) -> str:
    """Make customer text harmless inside our XML-style tags: a ticket can't 'close' <ticket> and add rules."""
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def parse(path: Path) -> Prompt:
    raw = path.read_text(encoding="utf-8")
    _, header, body = raw.split("---\n", 2)                      # file = --- header --- body
    meta = dict(line.split(": ", 1) for line in header.strip().splitlines())
    system, user = body.split("=== user ===\n")
    return Prompt(meta["name"], int(meta["version"]), meta, system.strip(), user.strip(), path)


def load(name: str, version: int | None = None) -> Prompt:
    """load("triage") -> the newest version; load("triage", 1) -> exactly v1."""
    versions = sorted((parse(p) for p in PROMPTS.glob(f"{name}_v*.md")), key=lambda p: p.version)
    if not versions:
        raise FileNotFoundError(f"No prompt files called {name}_v*.md in {PROMPTS}")
    if version is None:
        return versions[-1]
    for p in versions:
        if p.version == version:
            return p
    raise ValueError(f"{name} has versions {[p.version for p in versions]}, not {version}")


def all_prompts() -> list[Prompt]:
    return [parse(p) for p in sorted(PROMPTS.glob("*_v*.md"))]


def check_lock() -> list[str]:
    """Problems = prompts whose text changed without a new version number (or that were never locked)."""
    lock = json.loads(LOCK_FILE.read_text()) if LOCK_FILE.exists() else {}
    problems = []
    for p in all_prompts():
        key = f"{p.name}@v{p.version}"
        if key not in lock:
            problems.append(f"{key} is not locked yet: run `python prompt_kit.py --lock`")
        elif lock[key] != p.fingerprint:
            problems.append(f"{key} changed (fingerprint {lock[key]} -> {p.fingerprint}) but its version did not. "
                            "Bump the version in a NEW file, or re-lock if the change is intended.")
    return problems


def write_lock():
    LOCK_FILE.write_text(json.dumps({f"{p.name}@v{p.version}": p.fingerprint for p in all_prompts()}, indent=2) + "\n")


if __name__ == "__main__":
    if "--lock" in sys.argv:
        write_lock()
        print(f"Locked {len(all_prompts())} prompts in {LOCK_FILE.name}")
    for p in all_prompts():
        print(f"{p.name:8s} v{p.version}  fingerprint {p.fingerprint}  owner {p.meta.get('owner')}  "
              f"changed {p.meta.get('changed')}  ({len(p.system) // 4} tokens approx.)")
    problems = check_lock()
    print("Lock: OK" if not problems else "Lock problems:\n  " + "\n  ".join(problems))
