# sync.py: use CompanyClient against the mock systems, the way the Northwind assistant would.
#
#   (terminal 1)  uvicorn mock_systems:app --port 8100
#   (terminal 2)  python sync.py
#
# Credentials come from environment variables, never from the code you commit. The defaults below only
# work with the local mock.
import os
import uuid
from collections import Counter

from company_client import CompanyClient


def main():
    client = CompanyClient(
        base_url=os.getenv("NORTHWIND_API", "http://127.0.0.1:8100"),
        client_id=os.getenv("NORTHWIND_CLIENT_ID", "fde-assistant"),
        client_secret=os.getenv("NORTHWIND_CLIENT_SECRET", "assistant-secret-change-me"),
    )
    accounts = list(client.iter_accounts(page_size=20))
    print(f"CRM: {len(accounts)} accounts, tiers {dict(Counter(a['tier'] for a in accounts))}")

    open_tickets = list(client.iter_tickets(status="open"))
    print(f"HelpDesk: {len(open_tickets)} open tickets, "
          f"{sum('Where is my shipment' in t['subject'] for t in open_tickets)} of them WISMO")

    key = str(uuid.uuid4())                       # one key for this one logical action
    first = client.add_note(open_tickets[0]["id"], "Draft reply ready for review.", idempotency_key=key)
    again = client.add_note(open_tickets[0]["id"], "Draft reply ready for review.", idempotency_key=key)
    print(f"Note written: id {first['id']}; sent twice with the same Idempotency-Key -> same note id {again['id']}")
    print(f"Stats: {client.stats}")


if __name__ == "__main__":
    main()
