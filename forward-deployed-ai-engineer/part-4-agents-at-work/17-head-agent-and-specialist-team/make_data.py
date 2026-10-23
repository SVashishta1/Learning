"""make_data.py: create northwind.db, two months of (fictional) Northwind delivery data, plus ops notes and tickets.

python make_data.py         # writes northwind.db next to this file (same data every time: the random seed is fixed)

Something went wrong in September 2026. The data contains the clues; the agent team has to find them.
"""
import random
import sqlite3
from datetime import date, timedelta
from pathlib import Path

DB = Path(__file__).with_name("northwind.db")
REGIONS = {  # region: (hub, [(carrier, share of volume)], share of all shipments)
    "North": ("Leeds", [("SwiftHaul", 0.7), ("Parcelink", 0.3)], 0.35),
    "Midlands": ("Birmingham", [("Parcelink", 1.0)], 0.30),
    "South West": ("Bristol", [("CoastExpress", 1.0)], 0.20),
    "Scotland": ("Glasgow", [("ScotFreight", 1.0)], 0.15),
}
CUSTOMERS = [f"C-{n}" for n in (104, 205, 311, 418, 522, 630, 744, 851, 967)]


def working_days_after(d: date, n: int) -> date:
    while n > 0:
        d += timedelta(days=1)
        if d.weekday() < 5:
            n -= 1
    return d


def pick(rng, options):
    r, total = rng.random(), 0
    for value, weight in options:
        total += weight
        if r <= total:
            return value
    return options[-1][0]


def shipments(rng):
    rows, n = [], 0
    for month_start in (date(2026, 8, 1), date(2026, 9, 1)):
        day = month_start
        while day.month == month_start.month:
            if day.weekday() < 5:
                for _ in range(40):                                   # 40 collections per working day
                    n += 1
                    region = pick(rng, [(r, v[2]) for r, v in REGIONS.items()])
                    hub, carriers, _ = REGIONS[region]
                    carrier = pick(rng, carriers)
                    service = "Express" if rng.random() < 0.4 else "Standard"
                    promised = working_days_after(day, 1 if service == "Express" else 3)
                    dispatch_delay = 0
                    if hub == "Leeds" and date(2026, 9, 1) <= day <= date(2026, 9, 7) and rng.random() < 0.6:
                        dispatch_delay = rng.choice([1, 2])               # clue 1: Leeds hub system cutover
                    dispatched = working_days_after(day, dispatch_delay) if dispatch_delay else day
                    transit_late = rng.random() < 0.04                    # normal background lateness
                    if carrier == "SwiftHaul" and day >= date(2026, 9, 8):
                        transit_late = rng.random() < 0.38                # clue 2: SwiftHaul driver shortage
                    transit = (1 if service == "Express" else 3) + (rng.choice([1, 2]) if transit_late else 0)
                    delivered = working_days_after(dispatched, transit)
                    rows.append((f"NW-{60000 + n}", rng.choice(CUSTOMERS), region, hub, carrier, service, str(day),
                                 str(dispatched), str(promised), str(delivered), int(delivered <= promised)))
            day += timedelta(days=1)
    return rows


OPS_NOTES = [
    ("2026-08-12", "Parcelink", None, "Weekly call: all lanes green. Van fleet renewal on schedule."),
    ("2026-08-20", None, "Leeds", "Leeds hub: new warehouse management system (WMS) go-live planned for 1 Sep. Expect a short learning curve."),
    ("2026-08-28", "SwiftHaul", None, "SwiftHaul account review: on-time 96% in August. Contract renewal due December."),
    ("2026-09-02", None, "Leeds", "Leeds hub: WMS cutover issues. Scanning and label printing slow; outbound backlog of ~600 parcels."),
    ("2026-09-05", None, "Leeds", "Leeds hub: backlog down to ~150 parcels. Extra weekend shift approved."),
    ("2026-09-08", None, "Leeds", "Leeds hub: backlog cleared. WMS stable. Dispatch back to same-day."),
    ("2026-09-09", "SwiftHaul", None, "SwiftHaul: driver shortage at their Wakefield depot after a competitor opened nearby. About 30% of North routes uncovered this week."),
    ("2026-09-16", "SwiftHaul", None, "SwiftHaul: still short of drivers, recruiting agency staff. Asked for patience until mid-October."),
    ("2026-09-23", "CoastExpress", None, "CoastExpress: one van off the road for two days, covered by spare."),
    ("2026-09-29", "SwiftHaul", None, "SwiftHaul: no written recovery plan received yet despite two requests."),
]
TICKET_TEMPLATES = {
    "late_delivery": ["Parcel {id} is late and tracking hasn't moved since it left Leeds.",
                      "Second late Express this week ({id}). The SwiftHaul driver never turned up.",
                      "{id} promised yesterday, still not here. No tracking update for two days.",
                      "Our customers are complaining: {id} arrived two days late."],
    "damaged_goods": ["{id} arrived with a crushed box."],
    "billing": ["Question about the surcharge on our invoice."],
    "other": ["Can we add a new collection address?"],
}


def tickets(rng, ship_rows):
    rows, n = [], 0
    for month, late_share in (("2026-08", 0.02), ("2026-09", 0.08)):
        month_rows = [r for r in ship_rows if r[6].startswith(month)]
        for r in month_rows:
            late = r[10] == 0
            if (late and rng.random() < 0.45) or rng.random() < late_share * 0.1:
                n += 1
                category = "late_delivery" if late else rng.choice(["damaged_goods", "billing", "other"])
                text = rng.choice(TICKET_TEMPLATES[category]).format(id=r[0])
                rows.append((9000 + n, r[9], r[1], category, text))
    return rows


def main():
    rng = random.Random(17)
    DB.unlink(missing_ok=True)
    db = sqlite3.connect(DB)
    db.executescript("""
        CREATE TABLE shipments (id TEXT PRIMARY KEY, customer_id TEXT, region TEXT, hub TEXT, carrier TEXT,
            service TEXT, collected_date TEXT, dispatched_date TEXT, promised_date TEXT, delivered_date TEXT,
            on_time INTEGER);
        CREATE TABLE ops_notes (date TEXT, carrier TEXT, hub TEXT, note TEXT);
        CREATE TABLE tickets (id INTEGER PRIMARY KEY, created_date TEXT, customer_id TEXT, category TEXT, text TEXT);
    """)
    ship_rows = shipments(rng)
    db.executemany("INSERT INTO shipments VALUES (?,?,?,?,?,?,?,?,?,?,?)", ship_rows)
    db.executemany("INSERT INTO ops_notes VALUES (?,?,?,?)", OPS_NOTES)
    db.executemany("INSERT INTO tickets VALUES (?,?,?,?,?)", tickets(rng, ship_rows))
    db.commit()
    for month, total, on_time in db.execute(
            "SELECT substr(collected_date,1,7), COUNT(*), ROUND(100.0*AVG(on_time),1) FROM shipments GROUP BY 1"):
        print(f"{month}: {total} shipments, {on_time}% on time")
    print(f"Wrote {DB.name}")


if __name__ == "__main__":
    main()
