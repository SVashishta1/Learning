"""services.py: pretend external systems the workflow talks to: shipments (flaky), billing and email (idempotent).

python services.py      # show every credit issued and every email sent (check there are no duplicates)

Billing and email accept an IDEMPOTENCY KEY: if the same key arrives twice (because a workflow retried or resumed
after a crash), they return the first result instead of crediting or emailing twice. Real APIs like Stripe do this.
"""
import json
import random
import sqlite3
from pathlib import Path

DB = Path(__file__).with_name("services.db")

SHIPMENTS = {   # id: customer, tier, service, shipping fee, days late, email
    "NW-61204": ("Kestrel Pharmacy", "gold", "Express", 18.00, 1, "orders@kestrel-pharmacy.example"),
    "NW-61377": ("Brightside Tiles", "silver", "Standard", 42.00, 3, "ops@brightside-tiles.example"),
    "NW-61502": ("Harbour Fresh Foods", "gold", "Express", 26.00, 3, "logistics@harbourfresh.example"),
    "NW-61655": ("Pennine Outdoor Gear", "bronze", "Standard", 12.00, 1, "shop@pennine-outdoor.example"),
    "NW-61789": ("Kestrel Garden Centre", "bronze", "Express", 15.00, 2, "hello@kestrel-garden.example"),
}


class TransientError(Exception):
    """Worth retrying: timeouts, 503s, rate limits."""


class PermanentError(Exception):
    """Retrying won't help: not found, invalid input, no permission."""


_chaos = random.Random(7)          # the dice for random failures (seeded: the same run every time)


def get_shipment(shipment_id: str, fail_rate: float = 0.0) -> dict:
    if _chaos.random() < fail_rate:
        raise TransientError("503 Service Unavailable (shipments API)")
    if shipment_id not in SHIPMENTS:
        raise PermanentError(f"404 shipment {shipment_id} not found")
    customer, tier, service, fee, days_late, email = SHIPMENTS[shipment_id]
    return {"id": shipment_id, "customer": customer, "tier": tier, "service": service, "fee_gbp": fee,
            "days_late": days_late, "email": email}


def _db() -> sqlite3.Connection:
    db = sqlite3.connect(DB)
    db.execute("CREATE TABLE IF NOT EXISTS credits (idempotency_key TEXT PRIMARY KEY, customer TEXT, amount_gbp REAL, reason TEXT)")
    db.execute("CREATE TABLE IF NOT EXISTS outbox (idempotency_key TEXT PRIMARY KEY, recipient TEXT, subject TEXT, body TEXT)")
    return db


def issue_credit(idempotency_key: str, customer: str, amount_gbp: float, reason: str) -> dict:
    with _db() as db:
        row = db.execute("SELECT customer, amount_gbp FROM credits WHERE idempotency_key = ?", (idempotency_key,)).fetchone()
        if row:                                            # seen this key before: do NOT credit again
            return {"credited": row[1], "replayed": True}
        db.execute("INSERT INTO credits VALUES (?, ?, ?, ?)", (idempotency_key, customer, amount_gbp, reason))
    return {"credited": amount_gbp, "replayed": False}


def send_email(idempotency_key: str, recipient: str, subject: str, body: str) -> dict:
    with _db() as db:
        if db.execute("SELECT 1 FROM outbox WHERE idempotency_key = ?", (idempotency_key,)).fetchone():
            return {"sent": True, "replayed": True}
        db.execute("INSERT INTO outbox VALUES (?, ?, ?, ?)", (idempotency_key, recipient, subject, body))
    return {"sent": True, "replayed": False}


if __name__ == "__main__":
    with _db() as db:
        credits = db.execute("SELECT idempotency_key, customer, amount_gbp FROM credits ORDER BY rowid").fetchall()
        emails = db.execute("SELECT idempotency_key, recipient, subject FROM outbox ORDER BY rowid").fetchall()
    print(f"Credits issued ({len(credits)}):")
    for key, customer, amount in credits:
        print(f"  £{amount:6.2f}  {customer:24s} key={key}")
    print(f"Emails sent ({len(emails)}):")
    for key, to, subject in emails:
        print(f"  {to:34s} {subject[:50]!r}")
    print(json.dumps({"duplicate_credits": len(credits) - len({c[1] for c in credits})}))
