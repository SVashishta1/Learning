"""mock_api.py: pretend versions of Northwind's systems for the claims desk (like lesson 07, smaller).

    uvicorn mock_api:app --port 8100

    POST /oauth/token                       client credentials -> short-lived bearer token
    GET  /tms/shipments/{tracking}          shipment facts from the TMS read-only gateway (404 if unknown)
    GET  /helpdesk/tickets?queue=claims     new claim tickets
    GET  /helpdesk/tickets/{id}
    POST /helpdesk/tickets/{id}/notes       internal note (low risk: agents may write these directly)
    POST /helpdesk/tickets/{id}/replies     email to the CUSTOMER   (only after human approval)
    POST /finance/credits                   credit note = money     (only after human approval)
    GET  /admin/outbox                      what was "sent" (for demos and tests)
FAIL_RATE=0.2 makes 20% of GET requests fail with 503, so you can watch the client retry.
"""
import json
import os
import random
import secrets
import time
from pathlib import Path

from fastapi import Depends, FastAPI, Form, Header, HTTPException
from pydantic import BaseModel

DATA = Path(__file__).parent / "data"
SHIPMENTS = json.loads((DATA / "shipments.json").read_text(encoding="utf-8"))
TICKETS = {t["id"]: t for t in json.loads((DATA / "tickets.json").read_text(encoding="utf-8"))}
CLIENTS = {os.getenv("MOCK_CLIENT_ID", "claims-desk"): os.getenv("MOCK_CLIENT_SECRET", "claims-desk-secret-change-me")}
FAIL_RATE = float(os.getenv("FAIL_RATE", "0"))
dice = random.Random(42)
TOKENS: dict[str, float] = {}
OUTBOX: dict[str, list] = {"notes": [], "replies": [], "credits": []}
app = FastAPI(title="Northwind systems (mock)")


@app.post("/oauth/token")
def token(client_id: str = Form(), client_secret: str = Form(), grant_type: str = Form("client_credentials")):
    if CLIENTS.get(client_id) != client_secret or grant_type != "client_credentials":
        raise HTTPException(401, "invalid_client")
    tok = secrets.token_urlsafe(24)
    TOKENS[tok] = time.time() + 300
    return {"access_token": tok, "token_type": "Bearer", "expires_in": 300}


def auth(authorization: str = Header("")):
    tok = authorization.removeprefix("Bearer ")
    if TOKENS.get(tok, 0) < time.time():
        raise HTTPException(401, "invalid or expired token")


def flaky():
    if dice.random() < FAIL_RATE:
        raise HTTPException(503, "TMS gateway busy, try again")


@app.get("/healthz")
def health():
    return {"ok": True}


@app.get("/tms/shipments/{tracking}", dependencies=[Depends(auth), Depends(flaky)])
def shipment(tracking: str):
    if tracking not in SHIPMENTS:
        raise HTTPException(404, f"No shipment {tracking}")
    return {"tracking": tracking, **SHIPMENTS[tracking]}


@app.get("/helpdesk/tickets", dependencies=[Depends(auth), Depends(flaky)])
def tickets(queue: str = "claims", status: str = "new"):
    return [{k: t[k] for k in ("id", "subject", "received", "status")} for t in TICKETS.values()
            if t["queue"] == queue and t["status"] == status]


@app.get("/helpdesk/tickets/{ticket_id}", dependencies=[Depends(auth), Depends(flaky)])
def ticket(ticket_id: str):
    if ticket_id not in TICKETS:
        raise HTTPException(404, "No such ticket")
    return TICKETS[ticket_id]


class Note(BaseModel):
    text: str


class Credit(BaseModel):
    ticket_id: str
    tracking: str
    amount_eur: float
    approved_by: str


@app.post("/helpdesk/tickets/{ticket_id}/notes", dependencies=[Depends(auth)])
def note(ticket_id: str, n: Note):
    OUTBOX["notes"].append({"ticket_id": ticket_id, "text": n.text})
    return {"ok": True}


@app.post("/helpdesk/tickets/{ticket_id}/replies", dependencies=[Depends(auth)])
def reply(ticket_id: str, n: Note):
    OUTBOX["replies"].append({"ticket_id": ticket_id, "text": n.text})
    TICKETS[ticket_id]["status"] = "answered"
    return {"ok": True}


@app.post("/finance/credits", dependencies=[Depends(auth)])
def credit(c: Credit):
    if c.amount_eur <= 0:
        raise HTTPException(422, "amount must be positive")
    OUTBOX["credits"].append(c.model_dump())
    return {"ok": True, "credit_note": f"CN-{len(OUTBOX['credits']):05d}"}


@app.get("/admin/outbox")
def outbox():
    return OUTBOX


@app.post("/admin/reset")
def reset():
    """Back to the starting data (tests and demos)."""
    dice.seed(42)
    for t in TICKETS.values():
        t["status"] = "new"
    for v in OUTBOX.values():
        v.clear()
    return {"ok": True}
