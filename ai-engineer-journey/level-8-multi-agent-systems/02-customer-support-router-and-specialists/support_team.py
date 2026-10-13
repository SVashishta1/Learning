"""Project 8.2: a customer-support TEAM. A Router reads each message and hands it to the right Specialist.

  customer message -> Router (structured triage) -> Billing / Technical / Account specialist (each with its own tools)
                                                     specialists can HAND OFF to each other when needed
python support_team.py
"""
from typing import Literal

from pydantic import BaseModel, Field

import company_data as db
from agent_core import Agent, Tool, cost_report


# ---------------- Tools (each specialist only gets the tools it needs: least privilege) ----------------
class CustomerId(BaseModel):
    customer_id: str = Field(description="e.g. C-1001")


class RefundIn(BaseModel):
    invoice_id: str
    reason: str


class KbSearch(BaseModel):
    query: str


class TicketIn(BaseModel):
    customer_id: str
    summary: str
    priority: Literal["low", "normal", "high"]


class EmailUpdate(BaseModel):
    customer_id: str
    new_email: str


def get_customer(customer_id: str) -> str:
    c = db.CUSTOMERS.get(customer_id)
    return str(c) if c else f"No customer {customer_id}"


def list_invoices(customer_id: str) -> str:
    rows = [f"{k}: ${v['amount']} {v['status']} ({v['note']})" for k, v in db.INVOICES.items() if v["customer"] == customer_id]
    return "\n".join(rows) or "No invoices"


def issue_refund(invoice_id: str, reason: str) -> str:
    inv = db.INVOICES.get(invoice_id)
    if not inv:
        return f"No invoice {invoice_id}"
    if inv["status"] == "refunded":
        return "Already refunded."
    if inv["amount"] > db.REFUND_AUTO_LIMIT:          # policy enforced in CODE, not just in the prompt
        db.TICKETS.append({"type": "refund_review", "invoice": invoice_id, "reason": reason})
        return f"Refund of ${inv['amount']} exceeds the ${db.REFUND_AUTO_LIMIT} auto-limit; sent to a manager (ticket #{len(db.TICKETS)})."
    inv["status"] = "refunded"
    return f"Refunded ${inv['amount']} for {invoice_id}. Arrives in 3-5 business days."


def search_kb(query: str) -> str:
    words = set(query.lower().split())
    scored = sorted(db.KB, key=lambda a: -len(words & set((a["title"] + " " + a["body"]).lower().split())))
    return "\n".join(f"{a['id']} {a['title']}: {a['body']}" for a in scored[:2])


def create_ticket(customer_id: str, summary: str, priority: str) -> str:
    db.TICKETS.append({"customer": customer_id, "summary": summary, "priority": priority})
    return f"Created ticket #{len(db.TICKETS)} ({priority})"


def update_email(customer_id: str, new_email: str) -> str:
    if customer_id not in db.CUSTOMERS:
        return f"No customer {customer_id}"
    db.CUSTOMERS[customer_id]["email"] = new_email
    return f"Email updated to {new_email}"


# A special tool: lets a specialist pass the conversation to a colleague
class Handoff(BaseModel):
    to: Literal["billing", "technical", "account"]
    note: str = Field(description="What the next specialist needs to know")


HANDOFF_REQUEST: dict = {}


def handoff(to: str, note: str) -> str:
    HANDOFF_REQUEST.update(to=to, note=note)
    return f"Handing off to {to}. Finish with a one-line message telling the customer a colleague will continue."


T = {
    "get_customer": Tool("get_customer", "Look up a customer's profile and plan", CustomerId, get_customer),
    "list_invoices": Tool("list_invoices", "List a customer's invoices", CustomerId, list_invoices),
    "issue_refund": Tool("issue_refund", "Refund an invoice (policy limits apply)", RefundIn, issue_refund, needs_approval=True),
    "search_kb": Tool("search_kb", "Search help-centre articles", KbSearch, search_kb),
    "create_ticket": Tool("create_ticket", "Escalate to the human engineering team", TicketIn, create_ticket),
    "update_email": Tool("update_email", "Change the account email address", EmailUpdate, update_email, needs_approval=True),
    "handoff": Tool("handoff", "Transfer to another specialist when the issue is outside your area", Handoff, handoff),
}


# ---------------- The team ----------------
class Triage(BaseModel):
    category: Literal["billing", "technical", "account", "other"]
    urgency: Literal["low", "normal", "high"]
    sentiment: Literal["calm", "frustrated", "angry"]
    summary: str = Field(description="One sentence")


STYLE = "Be warm and brief. Verify facts with your tools before promising anything. Never invent policies."
ROUTER = Agent("Router", "You triage customer support messages for a cloud storage app.", effort="low")
SPECIALISTS = {
    "billing": Agent("Billing", f"You are the billing specialist. {STYLE}",
                     [T["get_customer"], T["list_invoices"], T["issue_refund"], T["handoff"]]),
    "technical": Agent("Technical", f"You are the technical support specialist. Use the knowledge base first; escalate with a ticket if it doesn't solve the problem. {STYLE}",
                       [T["search_kb"], T["create_ticket"], T["handoff"]]),
    "account": Agent("Account", f"You are the account specialist (profile, email, plan, data export). {STYLE}",
                     [T["get_customer"], T["update_email"], T["search_kb"], T["handoff"]]),
}


def handle(customer_id: str, message: str, max_handoffs: int = 2) -> str:
    triage = ROUTER.ask_structured(f"Customer {customer_id} wrote:\n{message}", Triage)
    team = triage.category if triage.category in SPECIALISTS else "technical"
    context = f"Customer id: {customer_id}\nTriage: {triage.model_dump()}\nMessage: {message}"
    replies = []
    for _ in range(max_handoffs + 1):
        HANDOFF_REQUEST.clear()
        replies.append(SPECIALISTS[team].run(context))
        if not HANDOFF_REQUEST:
            break
        context += f"\n\nNote from the {team} specialist: {HANDOFF_REQUEST['note']}"
        team = HANDOFF_REQUEST["to"]
    return "\n\n".join(replies)


if __name__ == "__main__":
    inbox = [
        ("C-1001", "Hi, I think I was charged twice for October?? Please fix this."),
        ("C-1002", "The app crashes every time I open it on my phone. Super annoying."),
        ("C-1003", "We were billed $249 but we only use 6 seats now. Can we get a refund for the difference?"),
        ("C-1001", "Please change my login email to priya.shah@newmail.com"),
    ]
    for cid, msg in inbox:
        print("\n" + "=" * 70 + f"\n📨 {cid}: {msg}")
        print(f"\n💬 Reply:\n{handle(cid, msg)}")
    print(f"\nTickets created: {db.TICKETS}")
    print(cost_report([ROUTER, *SPECIALISTS.values()]))
