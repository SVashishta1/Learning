# webhook_receiver.py: YOUR endpoint that HelpDesk calls when a ticket is created.
#
#   uvicorn webhook_receiver:app --port 8200
#
# Three defences every webhook receiver needs:
#   1. verify the signature  -> the message really comes from HelpDesk and wasn't changed
#   2. check the timestamp   -> an old message can't be replayed later
#   3. remember event ids    -> the same event delivered twice is processed once (senders DO retry)
# And one habit: answer fast (just store the event); do slow work (LLM calls) afterwards, in the background.
import json
import os

from fastapi import FastAPI, Header, HTTPException, Request

import signing

app = FastAPI(title="Northwind assistant: webhook receiver")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "whsec_demo_change_me")   # must match the sender's secret
PROCESSED = set()        # event ids we have already accepted (a database table in production)
RECEIVED = []            # accepted events, newest last


@app.post("/webhooks/helpdesk")
async def helpdesk_webhook(request: Request, x_northwind_signature: str = Header(None)):
    body = await request.body()                       # the RAW bytes: re-encoded JSON would break the signature
    try:
        signing.verify(WEBHOOK_SECRET, x_northwind_signature, body)
    except ValueError as reason:
        print(f"[webhook] REJECTED: {reason}")
        raise HTTPException(401, f"invalid signature: {reason}")
    event = json.loads(body)
    if event["id"] in PROCESSED:
        print(f"[webhook] duplicate {event['id']} ignored")
        return {"status": "duplicate"}
    PROCESSED.add(event["id"])
    RECEIVED.append(event)
    print(f"[webhook] accepted {event['id']}: {event['type']} -> ticket {event['data']['id']} "
          f"'{event['data']['subject']}'")
    return {"status": "accepted"}


@app.get("/webhooks/received")
def received():
    """Look at what arrived (handy while developing)."""
    return RECEIVED
