# send_webhook.py: play attacker (and clumsy sender) against your webhook receiver, to see each defence work.
#
#   python send_webhook.py good        a correctly signed event                 -> accepted
#   python send_webhook.py twice       the same event delivered twice           -> accepted, then duplicate
#   python send_webhook.py tampered    signed, then the body is changed         -> 401
#   python send_webhook.py replay      a valid signature from 10 minutes ago    -> 401
#   python send_webhook.py unsigned    no signature at all                      -> 401
#   python send_webhook.py wrong-secret signed with a guessed secret            -> 401
import json
import os
import sys
import time

import httpx

import signing

TARGET = os.getenv("WEBHOOK_TARGET", "http://127.0.0.1:8200/webhooks/helpdesk")
SECRET = os.getenv("WEBHOOK_SECRET", "whsec_demo_change_me")


def deliver(body, header):
    headers = {"Content-Type": "application/json", **({signing.HEADER: header} if header else {})}
    response = httpx.post(TARGET, content=body, headers=headers, timeout=5)
    print(f"  -> HTTP {response.status_code} {response.text}")


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "good"
    event = {"id": f"evt_demo_{mode}_{int(time.time())}", "type": "ticket.created", "created": int(time.time()),
             "data": {"id": 7, "subject": "Where is my shipment NW-4800007?", "status": "open"}}
    body = json.dumps(event).encode()
    print(f"Sending '{mode}' to {TARGET}")
    if mode == "good":
        deliver(body, signing.sign(SECRET, body))
    elif mode == "twice":
        header = signing.sign(SECRET, body)
        deliver(body, header)
        deliver(body, header)
    elif mode == "tampered":
        header = signing.sign(SECRET, body)
        deliver(body.replace(b"Where is my shipment", b"Refund me 10,000 EUR"), header)
    elif mode == "replay":
        deliver(body, signing.sign(SECRET, body, time.time() - 600))
    elif mode == "unsigned":
        deliver(body, None)
    elif mode == "wrong-secret":
        deliver(body, signing.sign("password123", body))
    else:
        sys.exit(f"Unknown mode {mode!r}. Use: good, twice, tampered, replay, unsigned, wrong-secret")


if __name__ == "__main__":
    main()
