"""Project 8.7: an agent that ACTS on your computer, safely.

Safety layers: sandbox (it can only touch ./workspace) · read-only tools run freely · every change needs
your approval (or --dry-run) · audit log of everything · step and budget limits.

python make_messy_folder.py
python organizer.py "Tidy up my downloads: group files into sensible folders, delete empty files and exact duplicates."
python organizer.py --dry-run "..."     # shows what it WOULD do, changes nothing
"""
import hashlib
import json
import shutil
import sys
from datetime import datetime
from pathlib import Path

from pydantic import BaseModel, Field

from agent_core import Agent, Tool, cli_approver, cost_report

SANDBOX = Path("workspace").resolve()
AUDIT_LOG = Path("audit_log.jsonl")
DRY_RUN = "--dry-run" in sys.argv


def safe_path(p: str) -> Path:
    """Resolve a path and REFUSE anything outside the sandbox (blocks ../../etc/passwd tricks)."""
    full = (SANDBOX / p).resolve()
    if full != SANDBOX and SANDBOX not in full.parents:
        raise PermissionError(f"{p} is outside the sandbox")
    return full


def audit(action: str, **details):
    with AUDIT_LOG.open("a") as f:
        f.write(json.dumps({"time": datetime.now().isoformat(timespec="seconds"), "action": action, "dry_run": DRY_RUN, **details}) + "\n")


# ---------- read-only tools (no approval needed) ----------
class PathIn(BaseModel):
    path: str = Field(description="Path relative to the workspace, e.g. 'downloads'")


def list_files(path: str) -> str:
    folder = safe_path(path)
    rows = []
    for f in sorted(folder.rglob("*")):
        if f.is_file():
            rows.append(f"{f.relative_to(SANDBOX)}  ({f.stat().st_size} bytes, md5 {hashlib.md5(f.read_bytes()).hexdigest()[:8]})")
    return "\n".join(rows) or "(empty)"


def read_file(path: str) -> str:
    return safe_path(path).read_text(errors="replace")[:2000]


# ---------- tools that CHANGE things (approval required) ----------
class MoveIn(BaseModel):
    source: str
    destination: str = Field(description="Destination path INCLUDING the file name")


def move_file(source: str, destination: str) -> str:
    src, dst = safe_path(source), safe_path(destination)
    if not src.exists():
        return f"{source} does not exist"
    if dst.exists():
        return f"{destination} already exists; choose another name"
    audit("move", source=source, destination=destination)
    if DRY_RUN:
        return f"[dry run] would move {source} -> {destination}"
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(src, dst)
    return f"Moved {source} -> {destination}"


def delete_file(path: str) -> str:
    target = safe_path(path)
    if not target.is_file():
        return f"{path} is not a file"
    audit("delete", path=path, size=target.stat().st_size)
    if DRY_RUN:
        return f"[dry run] would delete {path}"
    trash = SANDBOX / ".trash"                       # 'delete' = move to trash, so mistakes are reversible
    trash.mkdir(exist_ok=True)
    shutil.move(target, trash / f"{datetime.now():%H%M%S}_{target.name}")
    return f"Deleted {path} (recoverable from workspace/.trash)"


def approver(agent, tool, args):
    return True if DRY_RUN else cli_approver(agent, tool, args)


organizer = Agent(
    "Organizer",
    system=("You organise files in a sandboxed workspace. First LIST and inspect, then make a short plan, then act. "
            "Group files into clear folders (e.g. Images, Documents/Invoices, Installers). Only delete empty files or "
            "exact duplicates (same md5). If the human declines an action, respect it and continue with the rest. "
            "End with a summary table of what changed."),
    tools=[Tool("list_files", "List files with sizes and md5 hashes", PathIn, list_files),
           Tool("read_file", "Read the start of a text file", PathIn, read_file),
           Tool("move_file", "Move/rename a file (needs approval)", MoveIn, move_file, needs_approval=True),
           Tool("delete_file", "Delete a file (to trash; needs approval)", PathIn, delete_file, needs_approval=True)],
    approver=approver, max_steps=30, effort="medium")

if __name__ == "__main__":
    if not (SANDBOX / "downloads").exists():
        sys.exit("Run: python make_messy_folder.py")
    task = " ".join(a for a in sys.argv[1:] if a != "--dry-run") or \
        "Tidy up the 'downloads' folder: put files in sensible sub-folders, delete empty files and exact duplicates."
    print(organizer.run(task))
    print(f"\nAudit log: {AUDIT_LOG} | {'DRY RUN, nothing changed' if DRY_RUN else 'changes applied'}")
    print(cost_report([organizer]))
