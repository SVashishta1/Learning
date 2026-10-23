# mock_systems.py: pretend versions of Northwind's company systems, running on your laptop.
#
#   uvicorn mock_systems:app --port 8100
#
# It behaves like real enterprise APIs, including the annoying parts:
#   /oauth/token          OAuth2 "client credentials": swap a client id + secret for a short-lived access token
#   /crm/accounts         SalesCloud CRM: CURSOR pagination ("here is a bookmark, ask for the next page with it")
#   /helpdesk/tickets     HelpDesk: PAGE-NUMBER pagination ("page 2 of 5")
#   /helpdesk/tickets/{id}/notes   write an internal note (needs the tickets.write scope; supports Idempotency-Key)
#   rate limits (429 + Retry-After), random 503 errors, tokens that expire,
#   /admin/simulate/ticket-created  makes HelpDesk send a SIGNED webhook to a URL you choose.
import json
import os
import random
import secrets
import time

import httpx
from fastapi import Depends, FastAPI, Form, Header, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials

import signing

app = FastAPI(title="Northwind company systems (mock)")

# Registered API clients. In real life an admin creates these in the CRM's or identity provider's settings.
CLIENTS = {
    "fde-assistant": {"secret": "assistant-secret-change-me", "scopes": {"crm.read", "tickets.read", "tickets.write"}},
    "readonly-bot": {"secret": "readonly-secret-change-me", "scopes": {"crm.read", "tickets.read"}},
}
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "whsec_demo_change_me")
TOKEN_TTL = int(os.getenv("TOKEN_TTL", "300"))         # access tokens live 5 minutes
RATE_LIMIT = int(os.getenv("RATE_LIMIT", "5"))         # requests per client per second
FAIL_RATE = float(os.getenv("FAIL_RATE", "0.1"))       # share of GET requests that fail with 503
chaos = random.Random(7)                               # the dice for random failures (seeded: repeatable)
webhook_http = httpx.Client(timeout=5)                 # used to deliver webhooks (tests swap it)

TOKENS = {}          # access token -> {"client": ..., "scopes": ..., "expires_at": ...}
CALLS = {}           # (client, second) -> number of requests in that second
NOTES = {}           # ticket id -> list of notes
IDEMPOTENCY = {}     # Idempotency-Key -> the response we gave the first time

ACCOUNTS = [{"id": f"ACC-{n:04d}", "name": f"Customer {n}", "tier": ["gold", "silver", "bronze"][n % 3],
             "country": ["NL", "PL", "DE", "BE"][n % 4]} for n in range(1, 46)]
TICKETS = [{"id": n, "subject": f"Where is my shipment NW-{4800000 + n}?" if n % 5 else "Invoice question",
            "status": "open" if n % 3 else "closed", "account_id": ACCOUNTS[n % 45]["id"]} for n in range(1, 113)]


def now():
    return time.time()               # one place to read the clock, so tests can control time


# ---------- OAuth2 client credentials ----------

@app.post("/oauth/token")
def token(grant_type: str = Form(...), scope: str = Form(""), client_id: str = Form(None),
          client_secret: str = Form(None), basic: HTTPBasicCredentials = Depends(HTTPBasic(auto_error=False))):
    """Clients may send their id and secret as HTTP Basic auth (preferred by the spec) or as form fields."""
    if basic:
        client_id, client_secret = basic.username, basic.password
    if grant_type != "client_credentials":
        return JSONResponse({"error": "unsupported_grant_type"}, status_code=400)
    client = CLIENTS.get(client_id or "")
    if not client or not secrets.compare_digest(client["secret"], client_secret or ""):
        return JSONResponse({"error": "invalid_client"}, status_code=401)
    asked = set(scope.split()) or client["scopes"]          # no scope asked -> everything the client may have
    if not asked <= client["scopes"]:
        return JSONResponse({"error": "invalid_scope"}, status_code=400)
    access_token = secrets.token_urlsafe(24)
    TOKENS[access_token] = {"client": client_id, "scopes": asked, "expires_at": now() + TOKEN_TTL}
    return {"access_token": access_token, "token_type": "Bearer", "expires_in": TOKEN_TTL,
            "scope": " ".join(sorted(asked))}


def require(scope):
    """A FastAPI dependency: check the Bearer token, its expiry, its scope and the rate limit."""
    def check(request: Request, authorization: str = Header(None)):
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(401, "missing bearer token", headers={"WWW-Authenticate": "Bearer"})
        info = TOKENS.get(authorization[len("Bearer "):])
        if not info or info["expires_at"] < now():
            raise HTTPException(401, "invalid or expired token",
                                headers={"WWW-Authenticate": 'Bearer error="invalid_token"'})
        if scope not in info["scopes"]:
            raise HTTPException(403, f"token lacks scope {scope}",
                                headers={"WWW-Authenticate": f'Bearer error="insufficient_scope" scope="{scope}"'})
        window = (info["client"], int(now()))                # a new window every second
        CALLS[window] = CALLS.get(window, 0) + 1
        if CALLS[window] > RATE_LIMIT:
            raise HTTPException(429, "rate limit exceeded", headers={"Retry-After": "1"})
        if request.method == "GET" and chaos.random() < FAIL_RATE:
            raise HTTPException(503, "temporarily unavailable, try again")
        return info
    return check


# ---------- CRM: cursor pagination ----------

@app.get("/crm/accounts")
def accounts(limit: int = 20, cursor: str = None, auth=Depends(require("crm.read"))):
    start = int(cursor) if cursor else 0                    # real APIs make cursors opaque; ours is a position
    page = ACCOUNTS[start:start + min(limit, 50)]
    end = start + len(page)
    return {"data": page, "next_cursor": str(end) if end < len(ACCOUNTS) else None}


# ---------- HelpDesk: page-number pagination, writes, idempotency ----------

@app.get("/helpdesk/tickets")
def tickets(page: int = 1, per_page: int = 25, status: str = None, auth=Depends(require("tickets.read"))):
    rows = [t for t in TICKETS if status is None or t["status"] == status]
    per_page = min(per_page, 100)
    return {"tickets": rows[(page - 1) * per_page: page * per_page], "page": page, "per_page": per_page,
            "total": len(rows)}


@app.post("/helpdesk/tickets/{ticket_id}/notes", status_code=201)
def add_note(ticket_id: int, payload: dict, idempotency_key: str = Header(None),
             auth=Depends(require("tickets.write"))):
    """With the same Idempotency-Key, a retried request returns the first result instead of adding a duplicate."""
    if idempotency_key and idempotency_key in IDEMPOTENCY:
        return IDEMPOTENCY[idempotency_key]
    if not any(t["id"] == ticket_id for t in TICKETS):
        raise HTTPException(404, "no such ticket")
    note = {"id": sum(len(v) for v in NOTES.values()) + 1, "ticket_id": ticket_id,
            "body": str(payload.get("body", "")), "author": auth["client"]}
    NOTES.setdefault(ticket_id, []).append(note)
    if idempotency_key:
        IDEMPOTENCY[idempotency_key] = note
    return note


@app.get("/helpdesk/tickets/{ticket_id}/notes")
def list_notes(ticket_id: int, auth=Depends(require("tickets.read"))):
    return NOTES.get(ticket_id, [])


# ---------- webhooks: HelpDesk calls YOU when something happens ----------

@app.post("/admin/simulate/ticket-created")
def simulate_ticket_created(target: str, ticket_id: int = 1, times: int = 1):
    """Send a signed 'ticket.created' event to `target`. times=2 delivers it twice, like real retries do."""
    ticket = next((t for t in TICKETS if t["id"] == ticket_id), None)
    if not ticket:
        raise HTTPException(404, "no such ticket")
    event = {"id": f"evt_{ticket_id}_{int(now())}", "type": "ticket.created", "created": int(now()), "data": ticket}
    body = json.dumps(event).encode()                       # sign the exact bytes we send
    results = []
    for _ in range(times):
        response = webhook_http.post(target, content=body, headers={
            "Content-Type": "application/json", signing.HEADER: signing.sign(WEBHOOK_SECRET, body, now())})
        results.append(response.status_code)
    return {"event_id": event["id"], "delivered_status_codes": results}
