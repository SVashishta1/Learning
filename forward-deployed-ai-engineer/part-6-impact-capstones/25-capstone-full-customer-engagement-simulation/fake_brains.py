"""fake_brains.py: rule-based stand-ins for the model (FAKE_LLM=1). Same tools, same loop, no intelligence.
Replies use fixed templates in English, Dutch and Polish; the reason sentence stays in English in FAKE mode.
You can skip this file on a first read.
"""
import re

from llm import use_tool, use_tools

KIND_RULES = [("loss", r"never arrived|nooit aangekomen|niet ontvangen|missing|zaginę"),
              ("delay", r"delay|opóźnieni|vertraging|\blate\b"),
              ("damage", r"damag|broken|crushed|dented|scratched|beschadigd|uszkodz")]


def rule_extract(t: dict) -> dict:
    text = t["subject"] + " " + t["body"]
    low = text.lower()
    tracking = re.search(r"NW-\d{7}", text)
    amount = re.search(r"EUR\s*(\d{1,3}(?:[.,]\d{3})+|\d+)", text)
    lang = "nl" if re.search(r"\b(zending|goedemiddag|niet|nooit|graag)\b", low) else \
           "pl" if re.search(r"(dzień|przesyłk|prosimy)", low) else "en"
    return {"ticket_id": t["id"], "tracking": tracking.group(0) if tracking else "NW-0000000",
            "claim_type": next((k for k, rx in KIND_RULES if re.search(rx, low)), "damage"),
            "claimed_eur": float(re.sub(r"[.,]", "", amount.group(1))) if amount else None,
            "has_photos": bool(t["attachments"]) or "photos attached" in low, "language": lang,
            "summary": f"{t['subject']} (rule-based summary)"}


def triage_brain(view):
    if not view.called("list_new_claims"):
        return use_tool("list_new_claims")
    if not view.called("read_ticket"):
        return use_tools(*[("read_ticket", {"ticket_id": t["id"]}) for t in view.outputs("list_new_claims")[0]])
    if not view.called("record_claim"):
        return use_tools(*[("record_claim", rule_extract(t)) for t in view.outputs("read_ticket")])
    claims = view.outputs("record_claim")
    return use_tool("submit_report", claim_ids=[c["claim_id"] for c in claims],
                    suspicious_claim_ids=[c["claim_id"] for c in claims if c["suspicious"]], skipped=[])


def shipment_brain(view):
    if not view.called("list_claims"):
        return use_tool("list_claims")
    claims = view.outputs("list_claims")[0]
    if not view.called("fetch_shipment"):
        return use_tools(*[("fetch_shipment", {"claim_id": c["claim_id"]}) for c in claims])
    got = view.outputs("fetch_shipment")
    missing = [c["claim_id"] for c in claims if c["claim_id"] not in {g["claim_id"] for g in got}]
    if missing and sum(h["name"] == "fetch_shipment" for h in view.history) < 3 * len(claims):
        return use_tools(*[("fetch_shipment", {"claim_id": cid}) for cid in missing])   # the TMS was busy: try again
    return use_tool("submit_report", found=[g["claim_id"] for g in got if g["found"]],
                    not_found=[g["claim_id"] for g in got if not g["found"]],
                    notes=[f"{g['claim_id']}: POD '{g['pod_remark']}', {g['weight_kg']} kg, insured={g['insured']}"
                           for g in got if g["found"]])


QUERIES = {"damage": "damage photos proof of delivery time limits liability limit per kilogram",
           "loss": "loss lost expected delivery insured declared value time limits",
           "delay": "express delay compensation late shipping fee"}


def policy_brain(view):
    if not view.called("list_claims"):
        return use_tool("list_claims")
    claims = view.outputs("list_claims")[0]
    if not view.called("search_policy"):
        return use_tools(*[("search_policy", {"query": QUERIES[c["claim_type"]]}) for c in claims])
    if not view.called("record_basis"):
        return use_tools(*[("record_basis", {"claim_id": c["claim_id"], "chunk_ids": [h["chunk_id"] for h in hits],
                                             "rule": f"{c['claim_type']}: " + "; ".join(h["title"] for h in hits)})
                           for c, hits in zip(claims, view.outputs("search_policy"))])
    return use_tool("submit_report", basis=[{"claim_id": b["claim_id"], "chunk_ids": b["chunk_ids"], "rule": b["rule"]}
                                            for b in view.outputs("record_basis")])


def assessor_brain(view):
    if not view.called("list_claims"):
        return use_tool("list_claims")
    claims = view.outputs("list_claims")[0]
    if not view.called("assess"):
        return use_tools(*[("assess", {"claim_id": c["claim_id"]}) for c in claims])
    results = view.outputs("assess")
    payable = [r for r in results if r["outcome"].startswith("approve")]
    if payable and not view.called("propose_settlement"):
        return use_tools(*[("propose_settlement", {"claim_id": r["claim_id"]}) for r in payable])
    return use_tool("submit_report", decisions=[{"claim_id": r["claim_id"], "outcome": r["outcome"], "amount_eur": r["amount_eur"],
                                                 "explanation": "; ".join(r["reasons"])} for r in results],
                    settlement_action_ids=[p["action_id"] for p in view.outputs("propose_settlement")])


GREET = {"en": ("Dear customer,\n\nThank you for your claim about shipment {tracking}. ", "\n\nKind regards,\nNorthwind Claims"),
         "nl": ("Beste klant,\n\nBedankt voor uw claim over zending {tracking}. ", "\n\nMet vriendelijke groet,\nNorthwind Claims"),
         "pl": ("Szanowni Państwo,\n\nDziękujemy za reklamację dotyczącą przesyłki {tracking}. ",
                "\n\nZ poważaniem,\nDział Reklamacji Northwind")}
BODY = {
    "en": {"approve": "We have assessed it and will credit EUR {amount:.2f} to the bank account on your contract within 10 working days.",
           "reject": "Unfortunately we cannot accept it: {reason}. You can appeal within 14 days by replying to this email.",
           "need_info": "To assess it we need: {reason}. Please reply to this email with the missing information."},
    "nl": {"approve": "Wij hebben de claim beoordeeld en crediteren EUR {amount:.2f} binnen 10 werkdagen op de bankrekening uit uw contract.",
           "reject": "Helaas kunnen wij de claim niet accepteren: {reason}. U kunt binnen 14 dagen bezwaar maken door op deze e-mail te antwoorden.",
           "need_info": "Om de claim te beoordelen hebben wij nog nodig: {reason}. Wilt u de ontbrekende informatie in een antwoord op deze e-mail sturen?"},
    "pl": {"approve": "Po rozpatrzeniu przelejemy EUR {amount:.2f} na rachunek bankowy z Państwa umowy w ciągu 10 dni roboczych.",
           "reject": "Niestety nie możemy uznać reklamacji: {reason}. Mogą Państwo złożyć odwołanie w ciągu 14 dni, odpowiadając na tę wiadomość.",
           "need_info": "Aby rozpatrzyć reklamację, potrzebujemy: {reason}. Prosimy o odpowiedź na tę wiadomość z brakującymi informacjami."},
}


def reply_text(case: dict) -> str:
    c, a = case["claim"], case["assessment"]
    lang = c["language"] if c["language"] in BODY else "en"
    kind = "approve" if a["outcome"].startswith("approve") else a["outcome"]
    hello, bye = GREET[lang]
    return hello.format(tracking=c["tracking"]) + BODY[lang][kind].format(amount=a["amount_eur"], reason=a["reasons"][0]) + bye


def comms_brain(view):
    if not view.called("list_claims"):
        return use_tool("list_claims")
    claims = view.outputs("list_claims")[0]
    if not view.called("get_case"):
        return use_tools(*[("get_case", {"claim_id": c["claim_id"]}) for c in claims])
    cases = view.outputs("get_case")
    if not view.called("draft_reply"):
        return use_tools(*[("draft_reply", {"claim_id": k["claim"]["claim_id"], "language": k["claim"]["language"],
                                            "text": reply_text(k)}) for k in cases])
    if not view.called("propose_send_reply"):
        calls = [("propose_send_reply", {"claim_id": d["claim_id"]}) for d in view.outputs("draft_reply")]
        calls += [("add_internal_note", {"claim_id": k["claim"]["claim_id"],
                                         "text": f"AI desk: {k['assessment']['outcome']} EUR {k['assessment']['amount_eur']:.2f}. "
                                                 + ("SUSPICIOUS: the email contains payment instructions or orders; ignored. "
                                                    if k["claim"]["suspicious"] else "") + "Awaiting human approval."})
                  for k in cases]
        return use_tools(*calls)
    return use_tool("submit_report", reply_action_ids=[p["action_id"] for p in view.outputs("propose_send_reply")],
                    notes_added=len(view.outputs("add_internal_note")))


def make_lead_brain(desk, mission):
    order = [("triage", "Read every new claim ticket and record a structured claim for each."),
             ("shipment", "Fetch the TMS facts for every claim."),
             ("policy", "Find and record the policy sections that apply to every claim."),
             ("assessor", "Assess every claim with the policy rules and queue settlements for approval."),
             ("comms", "Draft a reply to every customer in their language, queue them, and add internal notes.")]

    def brain(view):
        for name, task in order:
            if not view.called(f"ask_{name}"):
                return use_tool(f"ask_{name}", task=task)
        a = desk.assessments
        risks = [f"{cid}: suspicious email (payment instructions or orders inside). Settlement limited to policy; verify sender."
                 for cid, c in desk.claims.items() if c["suspicious"]]
        risks += [f"{cid}: EUR {x['amount_eur']:.2f} is above EUR 1,000 and needs a claims supervisor" for cid, x in a.items()
                  if x["needs_supervisor"]]
        total = sum(x["amount_eur"] for x in a.values())
        return use_tool("submit_report",
                        summary=f"{len(a)} claims: {sum(x['outcome'].startswith('approve') for x in a.values())} to pay "
                                f"(EUR {total:.2f} in total), {sum(x['outcome'] == 'reject' for x in a.values())} to reject, "
                                f"{sum(x['outcome'] == 'need_info' for x in a.values())} need more information.",
                        decisions=[{"claim_id": cid, "outcome": x["outcome"], "amount_eur": x["amount_eur"],
                                    "needs_supervisor": x["needs_supervisor"]} for cid, x in a.items()],
                        actions_for_approval=[x.id for x in mission.actions if x.status == "pending"],
                        needs_info=[cid for cid, x in a.items() if x["outcome"] == "need_info"], risks=risks)
    return brain
