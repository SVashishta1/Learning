# northwind_api.py: a pretend version of Northwind's shipment and support systems (a small REST API).
#
#   uvicorn northwind_api:app --port 8200          (docs at http://localhost:8200/docs)
#
# Every request needs the header  X-Api-Key: <NORTHWIND_API_KEY>  (default: dev-key-change-me).
# Lesson 07 showed the harder parts of real company APIs (OAuth, rate limits, retries); this one stays simple
# so the lesson can focus on the TOOLS we build on top of it.
import os
import random
from datetime import date, timedelta

from fastapi import Depends, FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

API_KEY = os.getenv("NORTHWIND_API_KEY", "dev-key-change-me")
app = FastAPI(title="Northwind Logistics API (mock)")

CUSTOMERS = {
    "C-104": {"id": "C-104", "name": "Kestrel Pharmacy", "email": "orders@kestrel-pharmacy.example", "tier": "gold"},
    "C-205": {"id": "C-205", "name": "Brightside Tiles", "email": "ops@brightside-tiles.example", "tier": "silver"},
    "C-311": {"id": "C-311", "name": "Harbour Fresh Foods", "email": "logistics@harbourfresh.example", "tier": "gold"},
    "C-418": {"id": "C-418", "name": "Pennine Outdoor Gear", "email": "shop@pennine-outdoor.example", "tier": "bronze"},
    "C-522": {"id": "C-522", "name": "Kestrel Garden Centre", "email": "hello@kestrel-garden.example", "tier": "bronze"},
}
STATUSES = ["delivered", "delivered", "delivered", "in_transit", "delayed", "lost"]
HUBS = ["Leeds", "Bristol", "Manchester", "Glasgow", "Birmingham"]


def _make_shipments(seed: int = 4) -> dict:
    rng, out = random.Random(seed), {}
    for n in range(36):
        sid = f"NW-{58200 + n * 7}"
        status = rng.choice(STATUSES)
        promised = date(2026, 10, 1) + timedelta(days=rng.randint(0, 20))
        hub = rng.choice(HUBS)
        events = [{"date": str(promised - timedelta(days=2)), "event": "collected"},
                  {"date": str(promised - timedelta(days=1)), "event": f"arrived at {hub} hub"}]
        if status == "delivered":
            events.append({"date": str(promised), "event": "delivered"})
        elif status == "delayed":
            events.append({"date": str(promised), "event": f"delayed at {hub} hub: {rng.choice(['driver shortage', 'vehicle fault', 'missed trunk'])}"})
        elif status == "lost":
            events.append({"date": str(promised), "event": "no scan for 10 working days: declared lost"})
        out[sid] = {"id": sid, "customer_id": list(CUSTOMERS)[n % len(CUSTOMERS)], "service": rng.choice(["Express", "Standard"]),
                    "status": status, "promised": str(promised), "hub": hub, "events": events}
    return out


SHIPMENTS = _make_shipments()
TICKETS = {
    9001: {"id": 9001, "customer_id": "C-104", "status": "open", "subject": "Express parcels late again", "notes": []},
    9002: {"id": 9002, "customer_id": "C-205", "status": "open", "subject": "Broken tiles on delivery", "notes": []},
    9003: {"id": 9003, "customer_id": "C-104", "status": "closed", "subject": "Invoice question", "notes": []},
    9004: {"id": 9004, "customer_id": "C-311", "status": "open", "subject": "Chilled delivery temperature", "notes": []},
}
IDEMPOTENCY: dict[str, dict] = {}       # Idempotency-Key -> the note we created the first time


def check_key(x_api_key: str = Header(None)):
    if x_api_key != API_KEY:
        raise HTTPException(401, "missing or wrong X-Api-Key")


@app.get("/customers", dependencies=[Depends(check_key)])
def search_customers(q: str = "", limit: int = 5):
    q = q.lower()
    hits = [c for c in CUSTOMERS.values() if q in c["name"].lower() or q in c["email"].lower()]
    return {"items": hits[:limit], "total": len(hits)}


@app.get("/shipments", dependencies=[Depends(check_key)])
def list_shipments(customer_id: str, status: str | None = None, page: int = 1, page_size: int = 5):
    if customer_id not in CUSTOMERS:
        raise HTTPException(404, f"customer {customer_id} not found")
    rows = sorted((s for s in SHIPMENTS.values() if s["customer_id"] == customer_id and (not status or s["status"] == status)),
                  key=lambda s: s["promised"], reverse=True)          # newest first
    start = (page - 1) * page_size
    return {"items": [{k: s[k] for k in ("id", "service", "status", "promised")} for s in rows[start:start + page_size]],
            "page": page, "page_size": page_size, "total": len(rows)}


@app.get("/shipments/{shipment_id}", dependencies=[Depends(check_key)])
def get_shipment(shipment_id: str):
    if shipment_id not in SHIPMENTS:
        raise HTTPException(404, f"shipment {shipment_id} not found")
    return SHIPMENTS[shipment_id]


@app.get("/tickets", dependencies=[Depends(check_key)])
def list_tickets(customer_id: str, status: str | None = None):
    return {"items": [t for t in TICKETS.values() if t["customer_id"] == customer_id and (not status or t["status"] == status)]}


class NoteIn(BaseModel):
    text: str = Field(min_length=1, max_length=2000)


@app.post("/tickets/{ticket_id}/notes", status_code=201, dependencies=[Depends(check_key)])
def add_note(ticket_id: int, note: NoteIn, idempotency_key: str = Header(...)):
    if idempotency_key in IDEMPOTENCY:                      # a retry of a request we already did: same answer
        return IDEMPOTENCY[idempotency_key] | {"replayed": True}
    if ticket_id not in TICKETS:
        raise HTTPException(404, f"ticket {ticket_id} not found")
    created = {"ticket_id": ticket_id, "note_number": len(TICKETS[ticket_id]["notes"]) + 1, "text": note.text}
    TICKETS[ticket_id]["notes"].append(note.text)
    IDEMPOTENCY[idempotency_key] = created
    return created
