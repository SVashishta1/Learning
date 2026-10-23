# make_db.py: build northwind.db, a realistic (and realistically MESSY) copy of Northwind's data.
#
#   python make_db.py              -> creates northwind.db next to this file (replaces an old one)
#
# Real company data is never clean. On purpose, this database has:
#   - duplicate customers ("Brouwer Metals" and "BROUWER METALS ")
#   - the same value written many ways ("NL", "Netherlands", "nl"; "WISMO", "wismo", "Where is my shipment")
#   - missing values (NULL), dates in two formats, impossible weights, typos in IDs
#   - double-charged invoices
# It is generated with a fixed random seed, so everyone gets exactly the same data.
import random
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

DB = Path(__file__).parent / "northwind.db"
rng = random.Random(42)                                   # fixed seed = same "random" data every run
START = datetime(2026, 7, 1)

SCHEMA = """
CREATE TABLE customers (
    customer_id INTEGER PRIMARY KEY,
    name        TEXT NOT NULL,
    email       TEXT,
    country     TEXT,
    tier        TEXT,
    created_at  TEXT
);
CREATE TABLE shipments (
    shipment_id   TEXT PRIMARY KEY,
    customer_id   INTEGER REFERENCES customers(customer_id),
    origin        TEXT,
    destination   TEXT,
    created_at    TEXT,
    promised_date TEXT,
    delivered_at  TEXT,
    status        TEXT,
    weight_kg     REAL,
    price_eur     REAL
);
CREATE TABLE scans (
    scan_id     INTEGER PRIMARY KEY,
    shipment_id TEXT REFERENCES shipments(shipment_id),
    scanned_at  TEXT,
    location    TEXT,
    event       TEXT
);
CREATE TABLE tickets (
    ticket_id         INTEGER PRIMARY KEY,
    customer_id       INTEGER REFERENCES customers(customer_id),
    shipment_id       TEXT,
    created_at        TEXT,
    first_response_at TEXT,
    category          TEXT,
    subject           TEXT
);
CREATE TABLE invoices (
    invoice_id  INTEGER PRIMARY KEY,
    customer_id INTEGER REFERENCES customers(customer_id),
    shipment_id TEXT,
    amount_eur  REAL,
    issued_at   TEXT,
    paid_at     TEXT
);
"""

WORDS = ["Brouwer", "Hartmann", "Kowalska", "Van Dijk", "Nordic", "Delta", "Atlas", "Rijn", "Vistula", "Baltic",
         "Orion", "Maas", "Polar", "Zenith", "Hansa", "Alpine", "Tulip", "Amber", "Iron", "Harbour", "Vega", "Oak"]
KINDS = ["Metals", "Foods", "Trading", "Pharma", "Textiles", "Logistics", "Electronics", "Furniture", "Chemicals",
         "Paper", "Tools", "Plastics"]
COUNTRIES = {"NL": ["NL", "Netherlands", "nl", "NL "], "PL": ["PL", "Poland", "pl"], "DE": ["DE", "Germany"],
             "BE": ["BE", "Belgium"], "FR": ["FR", "France"]}
CITIES = {"NL": ["Rotterdam", "Utrecht", "Eindhoven"], "PL": ["Kraków", "Łódź", "Warsaw"],
          "DE": ["Düsseldorf", "Hamburg"], "BE": ["Antwerp", "Ghent"], "FR": ["Lille", "Paris"]}
# The true reason for each ticket, how often it happens, and the many ways agents typed the category.
TICKET_TYPES = [
    ("wismo", 0.41, ["WISMO", "wismo", "Where is my shipment", " WISMO", "where is my shipment"],
     ["Where is my shipment {s}?", "Pallet {s} not arrived", "Tracking {s} not updated", "Delivery status {s}"]),
    ("damage", 0.12, ["Damage", "damage", "DAMAGED"], ["Damaged goods {s}", "Boxes crushed in {s}"]),
    ("invoice", 0.18, ["Invoice", "invoice", "Billing"], ["Invoice question", "Charged twice?", "Wrong invoice amount"]),
    ("address_change", 0.09, ["Address change", "address"], ["Change delivery address {s}", "New address"]),
    ("other", 0.20, ["Other", "other", "General"], ["Question about your services", "Opening hours", "Account login"]),
]


def ts(moment):
    return moment.strftime("%Y-%m-%d %H:%M:%S")


def make_customers():
    rows, cid = [], 1
    names = rng.sample([f"{w} {k}" for w in WORDS for k in KINDS], 110)
    for name in names:
        code = rng.choice(list(COUNTRIES))
        tier = rng.choice(["gold", "silver", "silver", "bronze", "bronze", "bronze", None, "Gold"])
        email = f"orders@{name.lower().replace(' ', '')}.example"
        if rng.random() < 0.2:
            email = email.upper()                         # some emails were typed in capitals
        rows.append((cid, name, email, rng.choice(COUNTRIES[code]), tier,
                     ts(START - timedelta(days=rng.randint(30, 2000)))))
        cid += 1
    for original in rng.sample(rows[:], 10):              # 10 duplicates, created years apart by different people
        variant = rng.choice([original[1].upper() + " ", original[1] + " B.V.", " " + original[1].lower()])
        rows.append((cid, variant, None, original[3], None, ts(START - timedelta(days=rng.randint(1, 30)))))
        cid += 1
    return rows


def make_shipments(customers):
    rows, ids = [], set()
    for _ in range(3000):
        sid = f"NW-{rng.randint(1_000_000, 9_999_999)}"
        while sid in ids:
            sid = f"NW-{rng.randint(1_000_000, 9_999_999)}"
        ids.add(sid)
        customer = rng.choice(customers)
        code = next(c for c, variants in COUNTRIES.items() if customer[3] in variants)
        created = START + timedelta(minutes=rng.randint(0, 92 * 24 * 60))
        promised = (created + timedelta(days=rng.randint(2, 4))).date()
        status = rng.choices(["delivered", "in_transit", "delayed"], [0.85, 0.08, 0.07])[0]
        delivered = None
        if status == "delivered":
            delivered = datetime.combine(promised, datetime.min.time()) + timedelta(hours=rng.randint(-30, 40))
        if rng.random() < 0.03:
            status = rng.choice(["DELIVERED", "Delivered ", "delivred", "In Transit"]) if status != "delayed" else "Delayed"
        weight = round(rng.uniform(1, 800), 1)
        if rng.random() < 0.01:
            weight = rng.choice([0, -weight])            # impossible weights: a classic data-entry error
        promised_text = promised.isoformat()
        if rng.random() < 0.02:
            promised_text = promised.strftime("%d/%m/%Y")  # an old import used day/month/year
        rows.append((sid, customer[0], rng.choice(CITIES["NL"]), rng.choice(CITIES[code]), ts(created),
                     promised_text, ts(delivered) if delivered else None, status, weight,
                     round(abs(weight) * 0.9 + 20, 2)))
    return rows


def make_scans(shipments):
    rows, scan_id = [], 1
    for sid, _, origin, destination, created, _, delivered, status, _, _ in shipments:
        moment = datetime.strptime(created, "%Y-%m-%d %H:%M:%S") + timedelta(hours=rng.randint(1, 6))
        events = [("picked_up", origin), ("hub", "Rotterdam hub"), ("hub", f"{destination} depot")]
        if delivered:
            events += [("out_for_delivery", destination), ("delivered", destination)]
        elif status.lower().startswith("delayed"):
            events.append(("held", "Rotterdam hub"))
        for event, location in events:
            if event == "delivered":
                moment = datetime.strptime(delivered, "%Y-%m-%d %H:%M:%S")
            rows.append((scan_id, sid, ts(moment), location, event))
            scan_id += 1
            moment += timedelta(hours=rng.randint(3, 20))
    return rows


def make_tickets(customers, shipments):
    rows = []
    kinds, weights = [t[0] for t in TICKET_TYPES], [t[1] for t in TICKET_TYPES]
    by_kind = {t[0]: t for t in TICKET_TYPES}
    for tid in range(1, 2001):
        kind = rng.choices(kinds, weights)[0]
        _, _, labels, subjects = by_kind[kind]
        shipment = rng.choice(shipments)
        sid = shipment[0] if kind in ("wismo", "damage", "address_change") else None
        if sid and rng.random() < 0.02:
            sid = sid[:-1] + str((int(sid[-1]) + 1) % 10)   # a typo in the tracking number
        created = START + timedelta(minutes=rng.randint(0, 92 * 24 * 60))
        hours = rng.lognormvariate(2.95, 0.8)                  # median about 19 hours, with a long tail
        responded = None if rng.random() < 0.05 else ts(created + timedelta(hours=hours))
        label = None if rng.random() < 0.10 else rng.choice(labels)   # 10% of tickets have no category
        subject = rng.choice(subjects).format(s=sid or "")
        rows.append((tid, shipment[1], sid, ts(created), responded, label, subject.strip()))
    return rows


def make_invoices(shipments):
    rows, iid = [], 1
    for sid, cid, _, _, created, _, delivered, _, _, price in shipments:
        if not delivered:
            continue
        issued = datetime.strptime(delivered, "%Y-%m-%d %H:%M:%S") + timedelta(days=1)
        paid = None if rng.random() < 0.15 else ts(issued + timedelta(days=rng.randint(5, 45)))
        copies = 2 if rng.random() < 0.03 else 1              # 3% were charged twice by a billing bug
        for _ in range(copies):
            rows.append((iid, cid, sid, price, ts(issued), paid))
            iid += 1
    return rows


def main(path=DB):
    global rng
    rng = random.Random(42)                                   # reset the seed so every build is identical
    path = Path(path)
    if path.exists():
        path.unlink()                                         # start fresh every time
    con = sqlite3.connect(path)
    con.executescript(SCHEMA)
    customers = make_customers()
    shipments = make_shipments(customers)
    tables = {"customers": customers, "shipments": shipments, "scans": make_scans(shipments),
              "tickets": make_tickets(customers, shipments), "invoices": make_invoices(shipments)}
    for table, rows in tables.items():
        marks = ", ".join("?" * len(rows[0]))               # one ? placeholder per column
        con.executemany(f"INSERT INTO {table} VALUES ({marks})", rows)
    con.commit()
    con.close()
    print(f"Created {path.name}:")
    for table, rows in tables.items():
        print(f"  {table:<10} {len(rows):>6,} rows")


if __name__ == "__main__":
    main()
