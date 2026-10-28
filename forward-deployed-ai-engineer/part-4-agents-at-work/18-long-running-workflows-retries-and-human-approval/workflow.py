"""workflow.py: a durable, resumable "late-delivery compensation" workflow with retries and human approval.

python workflow.py start --run-id demo --offline       # start a run (offline: email drafts come from a template)
python workflow.py status demo                         # where is every item?
python approvals.py list                               # a person reviews the parked approvals ...
python approvals.py approve 1 --by alice               # ... and decides
python workflow.py resume demo --offline               # carry on from exactly where it stopped
Crash on purpose to see resuming work:  --crash-after 7   or   --crash-in issue_credit

For each late shipment:  fetch_shipment -> decide_credit -> draft_email -> approval -> issue_credit -> send_email
Every finished step is saved in workflow.db, so a crash, a restart or a 3-day wait for approval loses nothing.
"""
import argparse
import json
import os
import random
import re
import sqlite3
import time
from datetime import datetime, timezone
from pathlib import Path

from pydantic import BaseModel, Field

import llm
import services
from services import PermanentError, TransientError

DB = Path(__file__).with_name("workflow.db")
STEPS = ["fetch_shipment", "decide_credit", "draft_email", "approval", "issue_credit", "send_email"]
LATE_SHIPMENTS = ["NW-61204", "NW-61377", "NW-61502", "NW-61655", "NW-61789", "NW-69999"]
MAX_ATTEMPTS = 4
BASE_DELAY = 0.2                     # seconds; doubles after every failed attempt
APPROVAL_LIMIT_GBP = 10.0            # credits above this, or any goodwill credit, need a person's OK
SYMBOL = {"done": "✓", "waiting_approval": "…", "failed": "✗", "rejected": "⊘", "running": "↻", "pending": "·"}


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


# ---------------- 1. Durable state in SQLite ----------------
class Store:
    def __init__(self, path: Path = DB):
        self.db = sqlite3.connect(path)
        self.db.executescript("""
            CREATE TABLE IF NOT EXISTS runs (run_id TEXT PRIMARY KEY, created TEXT, items TEXT);
            CREATE TABLE IF NOT EXISTS steps (run_id TEXT, item TEXT, step TEXT, status TEXT, attempts INTEGER,
                result TEXT, error TEXT, updated TEXT, PRIMARY KEY (run_id, item, step));
            CREATE TABLE IF NOT EXISTS approvals (id INTEGER PRIMARY KEY AUTOINCREMENT, run_id TEXT, item TEXT,
                summary TEXT, status TEXT, decided_by TEXT, note TEXT, created TEXT, decided TEXT);""")

    def start_run(self, run_id: str, items: list[str]):
        with self.db:                                       # "with self.db" = one transaction, committed at the end
            self.db.execute("INSERT INTO runs VALUES (?, ?, ?)", (run_id, now(), json.dumps(items)))

    def items(self, run_id: str) -> list[str]:
        row = self.db.execute("SELECT items FROM runs WHERE run_id = ?", (run_id,)).fetchone()
        if not row:
            raise SystemExit(f"No run called {run_id!r}. Start one with: python workflow.py start --run-id {run_id}")
        return json.loads(row[0])

    def get(self, run_id: str, item: str, step: str) -> dict:
        row = self.db.execute("SELECT status, attempts, result, error FROM steps WHERE run_id=? AND item=? AND step=?",
                              (run_id, item, step)).fetchone()
        if not row:
            return {"status": "pending", "attempts": 0, "result": None, "error": None}
        return {"status": row[0], "attempts": row[1], "result": json.loads(row[2]) if row[2] else None, "error": row[3]}

    def save(self, run_id, item, step, status, attempts=0, result=None, error=None):
        with self.db:
            self.db.execute("INSERT INTO steps VALUES (?,?,?,?,?,?,?,?) ON CONFLICT (run_id, item, step) DO UPDATE SET "
                            "status=excluded.status, attempts=excluded.attempts, result=excluded.result, "
                            "error=excluded.error, updated=excluded.updated",
                            (run_id, item, step, status, attempts, json.dumps(result) if result is not None else None,
                             error, now()))

    def approval(self, run_id: str, item: str) -> dict | None:
        row = self.db.execute("SELECT id, status, decided_by, note FROM approvals WHERE run_id=? AND item=? "
                              "ORDER BY id DESC LIMIT 1", (run_id, item)).fetchone()
        return dict(zip(("id", "status", "decided_by", "note"), row)) if row else None

    def request_approval(self, run_id: str, item: str, summary: str) -> int:
        with self.db:
            cur = self.db.execute("INSERT INTO approvals (run_id, item, summary, status, created) VALUES (?,?,?,?,?)",
                                  (run_id, item, summary, "pending", now()))
        return cur.lastrowid


# ---------------- 2. The steps ----------------
def decide_credit(ship: dict) -> dict:
    """Policy in CODE, not in the model: money rules must be exact and testable."""
    amount, reasons = 0.0, []
    if ship["service"] == "Express":
        amount += 4.50
        reasons.append("Express surcharge refund (£4.50)")
    elif ship["days_late"] >= 2:
        amount += round(0.2 * ship["fee_gbp"], 2)
        reasons.append("20% of the Standard shipping fee (2+ days late)")
    goodwill = ship["tier"] == "gold" and ship["days_late"] >= 2
    if goodwill:
        amount += 15.0
        reasons.append("£15 goodwill credit for a gold customer")
    return {"amount_gbp": round(amount, 2), "reasons": reasons,
            "needs_approval": amount > APPROVAL_LIMIT_GBP or goodwill}


class Draft(BaseModel):
    subject: str = Field(description="Email subject, under 70 characters")
    body: str = Field(description="A short, warm apology email (under 120 words) that states the credit amount exactly")


def draft_email(ship: dict, credit: dict) -> dict:
    amount = f"£{credit['amount_gbp']:.2f}"
    prompt = (f"Customer: {ship['customer']}\nShipment: {ship['id']} ({ship['service']}), {ship['days_late']} working day(s) late\n"
              + (f"Credit to mention exactly: {amount} ({'; '.join(credit['reasons'])})" if credit["amount_gbp"]
                 else "Credit: none is due under our policy; do not offer or mention one."))
    reply = llm.chat(prompt, system="You write apology emails for Northwind Logistics customer service. "
                                    "Be specific, warm and brief. Never promise anything not listed.",
                     schema=Draft, model=llm.CHEAP_MODEL if llm.PROVIDER == "claude" else None, effort="low", max_tokens=800)
    if credit["amount_gbp"] and amount not in reply.parsed.body:     # check the model's work like any input
        raise TransientError(f"draft does not mention the exact amount {amount}; asking again")
    return reply.parsed.model_dump()


def run_step(step: str, ctx: dict, run_id: str, item: str, fail_rate: float) -> dict:
    if step == "fetch_shipment":
        return services.get_shipment(item, fail_rate)
    if step == "decide_credit":
        return decide_credit(ctx["fetch_shipment"])
    if step == "draft_email":
        return draft_email(ctx["fetch_shipment"], ctx["decide_credit"])
    if step == "issue_credit":
        credit = ctx["decide_credit"]
        if not credit["amount_gbp"]:
            return {"credited": 0, "skipped": True}
        return services.issue_credit(f"{run_id}:{item}:credit", ctx["fetch_shipment"]["customer"],
                                     credit["amount_gbp"], "; ".join(credit["reasons"]))
    if step == "send_email":
        return services.send_email(f"{run_id}:{item}:email", ctx["fetch_shipment"]["email"],
                                   ctx["draft_email"]["subject"], ctx["draft_email"]["body"])
    raise ValueError(step)


# ---------------- 3. The engine: advance every item as far as it can go ----------------
class Crash(Exception):
    pass


def advance(store: Store, run_id: str, fail_rate: float = 0.3, crash_after: int | None = None,
            crash_in: str | None = None, verbose: bool = True) -> dict:
    say = print if verbose else (lambda *a: None)
    completed = 0
    for item in store.items(run_id):
        ctx = {}
        for step in STEPS:
            state = store.get(run_id, item, step)
            if state["status"] == "done":
                ctx[step] = state["result"]                  # already done in an earlier run: reuse, don't redo
                continue
            if state["status"] in ("failed", "rejected"):
                break                                        # this item is finished (badly); a person must look
            if step == "approval":
                if not ctx["decide_credit"]["needs_approval"]:
                    store.save(run_id, item, step, "done", result={"auto_approved": True})
                    continue
                decision = store.approval(run_id, item)
                if decision is None:
                    credit = ctx["decide_credit"]
                    text = f"Credit £{credit['amount_gbp']:.2f} to {ctx['fetch_shipment']['customer']} ({'; '.join(credit['reasons'])})"
                    approval_id = store.request_approval(run_id, item, text)
                    store.save(run_id, item, step, "waiting_approval", result={"approval_id": approval_id})
                    say(f"[{item}] approval  … waiting for a person (approval #{approval_id}: {text})")
                    break
                if decision["status"] == "pending":
                    break                                    # still waiting: nothing to do for this item yet
                status = "done" if decision["status"] == "approved" else "rejected"
                store.save(run_id, item, step, status, result=decision)
                say(f"[{item}] approval  {SYMBOL[status]} {decision['status']} by {decision['decided_by']}")
                if status == "rejected":
                    break
                continue
            if state["status"] == "running":
                say(f"[{item}] {step}: was interrupted last time, running it again")
            attempts = state["attempts"]
            while True:
                attempts += 1
                store.save(run_id, item, step, "running", attempts)          # mark BEFORE doing the work
                try:
                    result = run_step(step, ctx, run_id, item, fail_rate)
                    if crash_in == step:
                        raise Crash(f"simulated crash inside {step}, after the side effect, before saving")
                    store.save(run_id, item, step, "done", attempts, result)
                    ctx[step] = result
                    extra = " (replayed: no duplicate)" if isinstance(result, dict) and result.get("replayed") else ""
                    say(f"[{item}] {step:14s} ✓ attempt {attempts}{extra}")
                    break
                except PermanentError as e:
                    store.save(run_id, item, step, "failed", attempts, error=str(e))
                    say(f"[{item}] {step:14s} ✗ {e} (permanent: not retried)")
                    break
                except TransientError as e:
                    if attempts >= MAX_ATTEMPTS:
                        store.save(run_id, item, step, "failed", attempts, error=f"gave up after {attempts} attempts: {e}")
                        say(f"[{item}] {step:14s} ✗ gave up after {attempts} attempts")
                        break
                    delay = BASE_DELAY * 2 ** (attempts - 1) * random.uniform(0.5, 1.5)   # backoff + jitter
                    say(f"[{item}] {step:14s} ! {e}; retry in {delay:.2f}s")
                    store.save(run_id, item, step, "running", attempts, error=str(e))
                    time.sleep(delay)
            if store.get(run_id, item, step)["status"] != "done":
                break
            completed += 1
            if crash_after is not None and completed >= crash_after:
                raise Crash(f"simulated crash after {completed} completed steps")
    return summary(store, run_id)


def summary(store: Store, run_id: str) -> dict:
    counts = {"complete": 0, "waiting_approval": 0, "failed": 0, "rejected": 0, "in_progress": 0}
    for item in store.items(run_id):
        states = [store.get(run_id, item, s)["status"] for s in STEPS]
        if all(s == "done" for s in states):
            counts["complete"] += 1
        else:
            first = next(s for s in states if s != "done")
            counts[first if first in counts else "in_progress"] += 1
    return counts


def print_status(store: Store, run_id: str):
    print(f"Run {run_id}   " + "  ".join(f"{s[:12]:12s}" for s in STEPS))
    for item in store.items(run_id):
        cells = []
        for s in STEPS:
            st = store.get(run_id, item, s)
            cells.append(f"{SYMBOL[st['status']]} {st['attempts'] or '':<10}")
        print(f"{item:10s} " + "  ".join(f"{c:12s}" for c in cells))
    print("Legend: ✓ done  … waiting for approval  ✗ failed  ⊘ rejected  ↻ interrupted  · not started  (number = attempts)")
    print("Summary:", json.dumps(summary(store, run_id)))


def offline_responder(request):
    """Stand-in for the email-writing model (a template, NOT AI)."""
    from fake_llm import json_reply
    prompt = request["messages"][-1]["content"]
    customer = re.search(r"Customer: (.+)", prompt).group(1)
    amount = re.search(r"exactly: (£[\d.]+)", prompt)
    shipment = re.search(r"Shipment: (NW-\d+)", prompt).group(1)
    credit = f" We have added a credit of {amount.group(1)} to your account." if amount else ""
    return json_reply({"subject": f"Sorry about your late delivery {shipment}",
                       "body": f"Dear {customer} team, we're sorry {shipment} arrived late.{credit} "
                               "Thank you for your patience. Northwind Customer Service"})


def main():
    p = argparse.ArgumentParser()
    p.add_argument("command", choices=["start", "resume", "status"])
    p.add_argument("run_id", nargs="?")
    p.add_argument("--run-id", dest="run_id_opt")
    p.add_argument("--offline", action="store_true", help="email drafts from a template instead of a model")
    p.add_argument("--fail-rate", type=float, default=0.3, help="share of shipment-API calls that fail (0-1)")
    p.add_argument("--crash-after", type=int, help="simulate a crash after N completed steps")
    p.add_argument("--crash-in", choices=STEPS, help="simulate a crash inside this step, after its side effect")
    args = p.parse_args()
    run_id = args.run_id or args.run_id_opt or datetime.now().strftime("run-%Y%m%d-%H%M%S")
    if args.offline:
        from fake_llm import FakeClaude
        llm.set_client(FakeClaude(responder=offline_responder))
    store = Store()
    if args.command == "status":
        print_status(store, run_id)
        return
    if args.command == "start":
        store.start_run(run_id, LATE_SHIPMENTS)
        print(f"Started run {run_id} with {len(LATE_SHIPMENTS)} late shipments")
    random.seed(1)
    try:
        result = advance(store, run_id, args.fail_rate, args.crash_after, args.crash_in)
    except Crash as e:
        print(f"💥 {e}. The process died here. Run: python workflow.py resume {run_id}")
        os._exit(1)                                          # die like a real crash: no clean-up code runs
    print("Summary:", json.dumps(result))
    if result["waiting_approval"]:
        print("Waiting for people: python approvals.py list")


if __name__ == "__main__":
    main()
