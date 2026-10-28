"""server.py: an MCP server that gives ANY AI app safe, well-designed tools over Northwind's API.

Run by an AI app (stdio):   python server.py            (it waits silently: the app talks to it via stdin/stdout)
Settings (environment variables):
  NORTHWIND_API_URL   where the API lives, e.g. http://localhost:8200. Default "inprocess": use northwind_api.py
                      directly inside this process, so you don't need a second terminal while learning.
  NORTHWIND_API_KEY   the API key the SERVER uses. The AI never sees it.
"""
import os
from typing import Annotated, Literal

import httpx
from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from mcp.types import ToolAnnotations
from pydantic import Field

API_URL = os.getenv("NORTHWIND_API_URL", "inprocess")
API_KEY = os.getenv("NORTHWIND_API_KEY", "dev-key-change-me")
PAGE_SIZE = 5

mcp = MCPServer("northwind", instructions=(
    "Tools for Northwind Logistics' customer, shipment and ticket systems. Typical flow: find_customers to get a "
    "customer ID (C-123) -> list_shipments / search_tickets with that ID -> get_shipment for details. "
    "IDs: customers C-123, shipments NW-12345, tickets 9001."))

_api = None


def api() -> httpx.Client:
    """One HTTP client for the whole server (connections are reused). Tests replace it."""
    global _api
    if _api is None:
        if API_URL == "inprocess":
            from fastapi.testclient import TestClient     # talks to the FastAPI app without a network
            import northwind_api
            _api = TestClient(northwind_api.app, headers={"X-Api-Key": API_KEY})
        else:
            _api = httpx.Client(base_url=API_URL, headers={"X-Api-Key": API_KEY}, timeout=10)
    return _api


def call(method: str, path: str, not_found_hint: str = "", **kwargs) -> dict:
    """Call the API and turn every failure into a SHORT message that tells the model what to do next."""
    try:
        r = api().request(method, path, **kwargs)
    except httpx.HTTPError:
        raise ToolError("The Northwind API is not reachable right now. Wait a moment and try once more; "
                        "if it still fails, tell the user the system is down.")
    if r.status_code == 404:
        raise ToolError(f"{r.json().get('detail', 'Not found')}. {not_found_hint}".strip())
    if r.status_code in (401, 403):
        raise ToolError("This server's access to the Northwind API was refused (a configuration problem). "
                        "Do not retry; tell the user an administrator must check the MCP server's API key.")
    if r.status_code == 422:
        raise ToolError(f"The API rejected the input: {r.json().get('detail')}")
    r.raise_for_status()
    return r.json()


# ---------------- Read tools ----------------
@mcp.tool(annotations=ToolAnnotations(read_only_hint=True))
def find_customers(
    query: Annotated[str, Field(description="Part of the company name or email domain, e.g. 'kestrel'", min_length=2)],
) -> str:
    """Find Northwind customers by company name or email domain. Use this FIRST when the user names a company:
    the other tools need the customer ID it returns (like C-104). Returns up to 5 matches."""
    data = call("GET", "/customers", params={"q": query, "limit": 5})
    if not data["items"]:
        return f"No customer matches '{query}'. Try a shorter part of the name."
    lines = [f"{c['id']}  {c['name']}  ({c['tier']} tier, {c['email'].split('@')[1]})" for c in data["items"]]
    more = f"\n({data['total'] - 5} more: use a more specific query)" if data["total"] > 5 else ""
    return "\n".join(lines) + more


@mcp.tool(annotations=ToolAnnotations(read_only_hint=True))
def list_shipments(
    customer_id: Annotated[str, Field(description="Customer ID from find_customers, like C-104", pattern=r"^C-\d{3}$")],
    status: Annotated[Literal["any", "in_transit", "delayed", "delivered", "lost"],
                      Field(description="Only shipments with this status")] = "any",
    page: Annotated[int, Field(description="Page number, starting at 1", ge=1)] = 1,
) -> str:
    """List one customer's shipments, newest first, 5 per page, optionally filtered by status.
    Use it to answer 'which of our parcels are late/lost?'. For the tracking history of one shipment, use get_shipment."""
    data = call("GET", "/shipments", not_found_hint="Use find_customers to get a valid customer ID.",
                params={"customer_id": customer_id, "status": None if status == "any" else status,
                        "page": page, "page_size": PAGE_SIZE})
    if not data["items"]:
        return f"{customer_id} has no shipments with status '{status}'."
    pages = -(-data["total"] // PAGE_SIZE)                  # round up
    lines = [f"{s['id']}  {s['status']:10s} {s['service']:8s} promised {s['promised']}" for s in data["items"]]
    footer = f"page {page} of {pages} ({data['total']} shipments)"
    if page < pages:
        footer += f"; call again with page={page + 1} for more"
    return "\n".join(lines + [footer])


@mcp.tool(annotations=ToolAnnotations(read_only_hint=True))
def get_shipment(
    shipment_id: Annotated[str, Field(description="Shipment ID like NW-58213 (NW, a dash, 5 digits)", pattern=r"^NW-\d{5}$")],
    detail: Annotated[Literal["summary", "full"], Field(description="summary = status line; full = every tracking event")] = "summary",
) -> str:
    """Get one shipment's status (summary) or its full tracking history (full). Use 'full' only when you need to
    explain WHY a shipment is late or lost; it returns more text."""
    s = call("GET", f"/shipments/{shipment_id}",
             not_found_hint="Check the ID, or use list_shipments(customer_id=...) to see real IDs.")
    line = f"{s['id']}: {s['status']} ({s['service']}), customer {s['customer_id']}, promised {s['promised']}, hub {s['hub']}"
    if detail == "summary":
        return line + f". Latest: {s['events'][-1]['event']} on {s['events'][-1]['date']}."
    return line + "\n" + "\n".join(f"  {e['date']}  {e['event']}" for e in s["events"])


@mcp.tool(annotations=ToolAnnotations(read_only_hint=True))
def search_tickets(
    customer_id: Annotated[str, Field(description="Customer ID like C-104", pattern=r"^C-\d{3}$")],
    status: Annotated[Literal["open", "closed", "any"], Field(description="Which tickets to include")] = "open",
) -> str:
    """List a customer's support tickets (open ones by default). Use before adding a note, to find the ticket ID."""
    data = call("GET", "/tickets", params={"customer_id": customer_id, "status": None if status == "any" else status})
    if not data["items"]:
        return f"No {status} tickets for {customer_id}."
    return "\n".join(f"{t['id']}  [{t['status']}]  {t['subject']}  ({len(t['notes'])} notes)" for t in data["items"])


# ---------------- Write tool ----------------
@mcp.tool(annotations=ToolAnnotations(read_only_hint=False, destructive_hint=False, idempotent_hint=True))
def add_ticket_note(
    ticket_id: Annotated[int, Field(description="Ticket number from search_tickets, like 9001")],
    note: Annotated[str, Field(description="The internal note, plain text, at most 1000 characters",
                               min_length=1, max_length=1000)],
    idempotency_key: Annotated[str, Field(description="Any unique string for THIS note, e.g. 'note-9001-late-review'. "
                                          "If you retry, reuse the same key and the note is not added twice",
                                          min_length=8, max_length=80)],
) -> str:
    """Add an INTERNAL note to a support ticket (customers don't see it). Only do this when the user asked you to
    record something. Safe to retry with the same idempotency_key."""
    data = call("POST", f"/tickets/{ticket_id}/notes", json={"text": note}, headers={"Idempotency-Key": idempotency_key},
                not_found_hint="Use search_tickets to find the right ticket ID.")
    again = " (this was a retry: no duplicate created)" if data.get("replayed") else ""
    return f"Added note #{data['note_number']} to ticket {ticket_id}{again}."


# ---------------- A resource and a prompt ----------------
@mcp.resource("northwind://guide")
def guide() -> str:
    """How Northwind's IDs, statuses and services work (read-only context an app can load)."""
    return ("Customers: C-123. Shipments: NW-12345, statuses in_transit, delayed, delivered, lost (no scan for "
            "10 working days). Services: Express (next working day by 17:00), Standard (3 working days). "
            "Tickets: 4-digit numbers; notes are internal.")


@mcp.prompt()
def investigate_late_shipments(company: str) -> str:
    """A ready-made task: find a company's delayed and lost shipments and explain why."""
    return (f"Find the customer '{company}' with find_customers. List their delayed and their lost shipments. "
            "For each one, call get_shipment with detail='full' and explain in one line why it is late. "
            "Finish with a short summary table. Do not add ticket notes unless I ask.")


if __name__ == "__main__":
    mcp.run()          # stdio transport: the AI app starts this process and talks to it through stdin/stdout
