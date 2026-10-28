"""guards.py: the defence layers. None of them trusts the model to resist an attack.

  1. separate   untrusted text goes inside <untrusted_document> tags, escaped, with a rule that it is data
  2. scan       look for injection signs in untrusted text (a warning light, never the only defence)
  3. allow-list the tools available depend on the TASK; with untrusted text in context: read-only tools only
  4. authorize  every tool call is checked against the logged-in customer's rights and limits (least privilege)
  5. check out  the final text is checked for leaks (system prompt canary, foreign emails, unknown links)
"""
import re
import secrets
import unicodedata
from dataclasses import dataclass

CREDIT_LIMIT_GBP = 50          # above this, a person must approve
ALLOWED_LINK_DOMAINS = {"northwind.example"}
CANARY = f"CANARY-{secrets.token_hex(4)}"     # a secret word hidden in the system prompt; must never be output


@dataclass
class Session:
    """Who is logged in. Tools act with THIS customer's rights, never the agent's own."""
    customer_id: str
    email: str
    credited_today: float = 0.0


# ---------- 1. Separation ----------
def wrap_untrusted(text: str, source: str) -> str:
    safe = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return f'<untrusted_document source="{source}">\n{safe}\n</untrusted_document>'


# ---------- 2. Scanning ----------
INJECTION_SIGNS = [
    (r"ignore (all |any )?(previous|prior|above|your) (instructions|rules)", "asks to ignore instructions"),
    (r"(system|developer) (prompt|note|message|override)", "pretends to be a system message"),
    (r"you are now|pretend (to be|you are)|act as (an? )?(admin|administrator|developer)", "tries to change your role"),
    (r"(issue|give|grant|apply) (a )?(credit|refund)", "asks for money"),
    (r"(send|forward|email) .{0,60}(to|@)", "asks to send something somewhere"),
    (r"!\[[^\]]*\]\(https?://", "contains a markdown image (a classic data-leak trick)"),
    (r"(print|reveal|show|repeat) .{0,30}(system prompt|instructions|rules)", "asks for the system prompt"),
]
HIDDEN_CHARS = re.compile(r"[​-‏‪-‮⁠-⁤﻿]")   # zero-width and direction marks


def scan(text: str) -> list[str]:
    """Return the warning signs found. An empty list does NOT mean safe: attackers rephrase."""
    findings = []
    if HIDDEN_CHARS.search(text):
        findings.append("contains invisible characters")
    plain = unicodedata.normalize("NFKC", HIDDEN_CHARS.sub("", text)).lower()
    findings += [why for pattern, why in INJECTION_SIGNS if re.search(pattern, plain)]
    return findings


# ---------- 3. Tool allow-lists ----------
READ_TOOLS = {"get_shipment", "search_policies"}
WRITE_TOOLS = {"issue_credit", "send_email"}


def allowed_tools(task: str, has_untrusted_content: bool) -> set[str]:
    if task == "summarise_document" or has_untrusted_content:
        return READ_TOOLS                     # reading someone else's text? then you can't act on the world
    if task == "customer_chat":
        return READ_TOOLS | WRITE_TOOLS
    return set()


# ---------- 4. Least-privilege authorisation of every call ----------
def authorize(tool: str, args: dict, session: Session, shipments: dict) -> tuple[str, str]:
    """Returns (decision, reason). decision is 'allow', 'deny' or 'needs_approval'."""
    if tool == "get_shipment":
        s = shipments.get(args.get("shipment_id", ""))
        if s and s["customer_id"] != session.customer_id:
            return "deny", "that shipment belongs to another customer"
    if tool == "issue_credit":
        if args.get("customer_id") != session.customer_id:
            return "deny", "credits can only go to the logged-in customer's account"
        amount = float(args.get("amount_gbp", 0))
        if amount <= 0:
            return "deny", "amount must be positive"
        if session.credited_today + amount > CREDIT_LIMIT_GBP:
            return "needs_approval", f"total credit today would exceed £{CREDIT_LIMIT_GBP}"
    if tool == "send_email" and args.get("to", "").lower() != session.email.lower():
        return "deny", "emails can only go to the customer's address on file"
    return "allow", ""


# ---------- 5. Output checks ----------
EMAIL = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")
LINK = re.compile(r"https?://([\w.-]+)")
SECRETS = re.compile(r"sk-ant-[\w-]{10,}|AKIA[0-9A-Z]{16}")


def check_output(text: str, session: Session) -> tuple[str, list[str]]:
    """Returns (safe_text, problems). Leaky parts are replaced, and the whole reply is withheld on a canary leak."""
    problems = []
    if CANARY in text:
        return "Sorry, I can't help with that.", ["system prompt leak (canary found)"]
    for address in set(EMAIL.findall(text)):
        if address.lower() != session.email.lower():
            problems.append(f"foreign email address removed: {address}")
            text = text.replace(address, "[removed]")
    for domain in set(LINK.findall(text)):
        if domain.lower() not in ALLOWED_LINK_DOMAINS:
            problems.append(f"link to unknown domain removed: {domain}")
            text = re.sub(rf"!?\[[^\]]*\]\(https?://{re.escape(domain)}[^)]*\)|https?://{re.escape(domain)}\S*", "[link removed]", text)
    if SECRETS.search(text):
        problems.append("secret-looking string removed")
        text = SECRETS.sub("[removed]", text)
    return text, problems
