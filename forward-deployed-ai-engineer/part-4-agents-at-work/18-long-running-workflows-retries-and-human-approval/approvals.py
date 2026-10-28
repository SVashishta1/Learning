"""approvals.py: the human approval queue. People decide here; the workflow picks the decision up on its next resume.

python approvals.py list                                   # what's waiting?
python approvals.py approve 1 --by alice                    # approve request #1
python approvals.py reject 2 --by alice --note "Already credited by phone"
"""
import argparse

from workflow import Store, now


def main():
    p = argparse.ArgumentParser()
    p.add_argument("command", choices=["list", "approve", "reject"])
    p.add_argument("id", nargs="?", type=int)
    p.add_argument("--by", help="who is deciding (recorded for the audit trail)")
    p.add_argument("--note", default="")
    args = p.parse_args()
    store = Store()
    if args.command == "list":
        rows = store.db.execute("SELECT id, run_id, item, summary, status, decided_by FROM approvals ORDER BY id").fetchall()
        if not rows:
            print("No approval requests.")
        for id_, run_id, item, summary, status, by in rows:
            print(f"#{id_:<3} {status:9s} {run_id:8s} {item:9s} {summary}" + (f"  (by {by})" if by else ""))
        return
    if not args.id or not args.by:
        raise SystemExit("Give the request number and who you are, e.g.: python approvals.py approve 1 --by alice")
    with store.db:
        changed = store.db.execute("UPDATE approvals SET status=?, decided_by=?, note=?, decided=? WHERE id=? AND status='pending'",
                                   ("approved" if args.command == "approve" else "rejected", args.by, args.note, now(), args.id)).rowcount
    if not changed:
        raise SystemExit(f"Request #{args.id} doesn't exist or was already decided.")
    decision = "approved" if args.command == "approve" else "rejected"
    print(f"#{args.id} {decision} by {args.by}. Now run: python workflow.py resume <run id>")


if __name__ == "__main__":
    main()
