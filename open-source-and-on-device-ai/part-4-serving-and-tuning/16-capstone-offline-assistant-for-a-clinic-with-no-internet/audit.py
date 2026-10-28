"""A tamper-evident audit log: every question and answer is one JSON line, chained with SHA-256 hashes.

Each record stores the hash of the record before it. Changing or deleting any old line breaks the chain,
and `verify()` finds exactly where.

Run:  python audit.py verify       (check the whole chain)
      python audit.py show 5       (print the last 5 records)
"""
import hashlib
import json
import os
import sys
import threading
from datetime import datetime, timezone
from pathlib import Path

LOG = Path(os.environ.get("DATA_DIR", Path(__file__).parent / "data")) / "audit.jsonl"
GENESIS = "0" * 64                    # the "previous hash" of the very first record
_lock = threading.Lock()              # two requests at the same moment must not interleave their lines


def _hash(record):
    """SHA-256 of the record's content (without its own hash), written in a fixed key order."""
    content = {k: v for k, v in record.items() if k != "hash"}
    return hashlib.sha256(json.dumps(content, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def _last_hash():
    if not LOG.exists() or LOG.stat().st_size == 0:
        return GENESIS
    with LOG.open("rb") as f:
        last_line = f.read().splitlines()[-1]
    return json.loads(last_line)["hash"]


def log(event):
    """Append one event (a dict) to the log and return the stored record."""
    with _lock:
        LOG.parent.mkdir(parents=True, exist_ok=True)
        record = {"time": datetime.now(timezone.utc).isoformat(timespec="seconds"), **event,
                  "prev_hash": _last_hash()}
        record["hash"] = _hash(record)
        with LOG.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
        return record


def verify():
    """Return (ok, message). Checks every record's own hash and its link to the previous record."""
    if not LOG.exists():
        return True, "No audit log yet."
    previous = GENESIS
    lines = LOG.read_text(encoding="utf-8").splitlines()
    for number, line in enumerate(lines, start=1):
        record = json.loads(line)
        if record.get("prev_hash") != previous:
            return False, f"Line {number}: the link to the previous record is broken (a line was removed or reordered)."
        if _hash(record) != record.get("hash"):
            return False, f"Line {number}: the content was changed after it was written."
        previous = record["hash"]
    return True, f"All {len(lines)} records are intact."


if __name__ == "__main__":
    command = sys.argv[1] if len(sys.argv) > 1 else "verify"
    if command == "verify":
        ok, message = verify()
        print(("✅ " if ok else "❌ ") + message)
        sys.exit(0 if ok else 1)
    elif command == "show":
        count = int(sys.argv[2]) if len(sys.argv) > 2 else 5
        lines = LOG.read_text(encoding="utf-8").splitlines() if LOG.exists() else []
        for line in lines[-count:]:
            r = json.loads(line)
            print(f"{r['time']}  {r.get('staff_id', '?'):<8} {r.get('event', '?'):<8} {r.get('question', '')[:60]}")
    else:
        sys.exit("Usage: python audit.py verify | show [N]")
