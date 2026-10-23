"""claims_tools.py: the claims desk's facts, in plain Python (no AI).

  PolicyIndex   BM25 search over Northwind's (fictional) policy documents, with chunk ids for citations
  assess()      the settlement rules from the claims policy: code calculates every euro
  Desk          the shared state of one run: claims, shipment facts, policy basis, assessments, drafts
"""
import math
import re
from collections import Counter
from datetime import date, datetime
from pathlib import Path

HERE = Path(__file__).parent
AS_OF = date.fromisoformat("2026-10-22")       # "today" for the simulation, so results never change
EUR_PER_KG = 10
HANDLER_LIMIT_EUR = 1000
INJECTION = re.compile(r"ignore (all |your )?(previous|prior) instructions|authori[sz]ed by (your|the) ceo|\bIBAN\b",
                       re.IGNORECASE)


class PolicyIndex:
    def __init__(self, folder: Path = HERE / "policies"):
        self.chunks = []
        for path in sorted(folder.glob("*.md")):
            for section in re.split(r"\n(?=## )", path.read_text(encoding="utf-8")):
                if section.startswith("## "):
                    title = section.splitlines()[0][3:].strip()
                    self.chunks.append({"chunk_id": f"{path.stem}#{re.sub(r'[^a-z]+', '-', title.lower()).strip('-')}",
                                        "title": title, "text": " ".join(section.splitlines()[1:]).strip()})
        self.tokens = [re.findall(r"[a-z0-9]+", (c["title"] + " " + c["text"]).lower()) for c in self.chunks]
        self.avg = sum(map(len, self.tokens)) / len(self.tokens)
        self.df = Counter(w for t in self.tokens for w in set(t))

    def search(self, query: str, k: int = 3) -> list[dict]:
        q, n, out = re.findall(r"[a-z0-9]+", query.lower()), len(self.chunks), []
        for c, toks in zip(self.chunks, self.tokens):
            tf = Counter(toks)
            score = sum(math.log(1 + (n - self.df[w] + 0.5) / (self.df[w] + 0.5)) * tf[w] * 2.2
                        / (tf[w] + 1.2 * (0.25 + 0.75 * len(toks) / self.avg)) for w in q if w in tf)
            if score > 0:
                out.append({**c, "score": round(score, 2)})
        return sorted(out, key=lambda c: -c["score"])[:k]

    def ids(self) -> set[str]:
        return {c["chunk_id"] for c in self.chunks}


def _day(ts: str | None) -> date | None:
    return datetime.fromisoformat(ts).date() if ts else None


def assess(claim: dict, shipment: dict | None) -> dict:
    """The claims policy as code. Returns outcome, amount, reasons and the policy sections used."""
    def result(outcome, amount, reasons, sources):
        amount = round(amount, 2)
        return {"claim_id": claim["claim_id"], "outcome": outcome, "amount_eur": amount, "reasons": reasons,
                "policy_refs": sources, "needs_supervisor": amount > HANDLER_LIMIT_EUR,
                "suspicious": claim.get("suspicious", False)}

    if shipment is None:
        return result("need_info", 0, [f"No shipment {claim['tracking']} in the TMS: ask the customer to check the number"],
                      ["claims-policy#evidence-required"])
    received = _day(claim["received"])
    limit = shipment["declared_value_eur"] if shipment["insured"] else min(EUR_PER_KG * shipment["weight_kg"],
                                                                           shipment["declared_value_eur"])
    limit_ref = "claims-policy#insured-shipments" if shipment["insured"] else "claims-policy#liability-limit"
    kind = claim["claim_type"]
    if kind == "damage":
        if not claim["has_photos"]:
            return result("need_info", 0, ["Damage claims need photos of the goods and packaging"],
                          ["claims-policy#evidence-required"])
        delivered = _day(shipment["delivered_at"])
        noted = bool(re.search(r"damag|dent|broken|crush", shipment["pod_remark"], re.IGNORECASE))
        days = (received - delivered).days
        if (not noted and days > 7) or days > 30:
            return result("reject", 0, [f"Reported {days} days after delivery; POD says '{shipment['pod_remark'] or 'nothing'}'. "
                                        "Visible damage must be on the POD or reported within 7 days"],
                          ["claims-policy#time-limits", "delivery-terms#proof-of-delivery"])
    elif kind == "loss":
        if shipment["delivered_at"]:
            return result("need_info", 0, ["The TMS shows this shipment as delivered: ask for details and check the POD"],
                          ["delivery-terms#proof-of-delivery"])
        overdue = (AS_OF - date.fromisoformat(shipment["expected_delivery"])).days
        if overdue < 7:
            return result("need_info", 0, [f"Only {overdue} days overdue; it counts as lost after 7 days"],
                          ["claims-policy#time-limits"])
        if (received - date.fromisoformat(shipment["expected_delivery"])).days > 30:
            return result("reject", 0, ["Loss reported more than 30 days after the expected delivery date"],
                          ["claims-policy#time-limits"])
    elif kind == "delay":
        expected_end = datetime.fromisoformat(shipment["expected_delivery"] + "T23:59")
        late_h = (datetime.fromisoformat(shipment["delivered_at"]) - expected_end).total_seconds() / 3600 \
            if shipment["delivered_at"] else 0
        if shipment["service"] == "express" and late_h > 48:
            return result("approve_full", shipment["shipping_fee_eur"],
                          [f"Express delivered {late_h:.0f} h late: refund the Express fee"],
                          ["claims-policy#delay-compensation", "delivery-terms#express-service"])
        return result("reject", 0, [f"{shipment['service'].title()} service, {max(late_h, 0):.0f} h late: no delay compensation"],
                      ["claims-policy#delay-compensation"])
    claimed = claim["claimed_eur"]
    if claimed is None:
        return result("need_info", 0, ["The claim does not say an amount"], ["claims-policy#evidence-required"])
    if claimed <= limit:
        return result("approve_full", claimed, [f"Claimed {claimed:.0f} is within the limit of {limit:.0f}"], [limit_ref])
    return result("approve_partial", limit, [f"Claimed {claimed:.0f} is above the limit of {limit:.0f}: pay the limit"],
                  [limit_ref])


class Desk:
    """Everything one run of the claims desk knows."""

    def __init__(self, client):
        self.client = client
        self.index = PolicyIndex()
        self.claims: dict[str, dict] = {}
        self.shipments: dict[str, dict | None] = {}
        self.policy_basis: dict[str, list[str]] = {}
        self.assessments: dict[str, dict] = {}
        self.drafts: dict[str, dict] = {}

    def record_claim(self, ticket_id, tracking, claim_type, claimed_eur, has_photos, language, summary, suspicious=False):
        t = self.client.ticket(ticket_id)                           # raises KeyError if the ticket doesn't exist
        if not re.fullmatch(r"NW-\d{7}", tracking):
            raise ValueError("Tracking numbers look like NW-1234567")
        claim = {"claim_id": f"C-{ticket_id[2:]}", "ticket_id": ticket_id, "tracking": tracking, "claim_type": claim_type,
                 "claimed_eur": claimed_eur, "has_photos": has_photos, "language": language, "summary": summary,
                 "received": t["received"], "suspicious": suspicious or bool(INJECTION.search(t["body"]))}
        self.claims[claim["claim_id"]] = claim
        return claim

    def fetch_shipment(self, claim_id):
        c = self.claims[claim_id]
        try:
            self.shipments[claim_id] = self.client.shipment(c["tracking"])
        except KeyError:
            self.shipments[claim_id] = None
            return {"claim_id": claim_id, "found": False, "note": f"{c['tracking']} is not in the TMS"}
        return {"claim_id": claim_id, "found": True, **self.shipments[claim_id]}

    def assess(self, claim_id):
        if claim_id not in self.shipments:
            raise ValueError("Fetch the shipment first (the shipment agent).")
        self.assessments[claim_id] = assess(self.claims[claim_id], self.shipments[claim_id])
        return self.assessments[claim_id]
