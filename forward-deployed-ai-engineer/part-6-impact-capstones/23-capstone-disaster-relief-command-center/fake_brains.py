"""fake_brains.py: rule-based stand-ins for the model, used when FAKE_LLM=1.

They call the SAME tools in the same loop a real model would, so FAKE mode exercises all the plumbing
(tools, checks, budgets, approvals, the web page) for free and gives the same answer every time.
They are deliberately simple keyword rules: a real model reads messy, multilingual reports far better.
You can skip this file on a first read.
"""
import math
import re

from llm import use_tool, use_tools
from relief_tools import INJECTION, NOT_STOCKED

# ---------------------------------------------------------------- intake: keyword rules
NEED_RULES = {
    "rescue": r"\bboats?\b|on roofs|trapped|\bstuck\b|waving",
    "water": r"(drinking|clean) water|agua|needs?:[^.]*\bwater\b",
    "food": r"\bfood\b(?! ok)|comida",
    "medical": r"medical|dressings|first.aid|medicine",
    "fuel": r"\bfuel\b",
    "blankets": r"blanket",
    "hygiene": r"hygiene",
    "tarps": r"\btarps?\b",
    "shelter": r"no shelter|homeless",
}
VULNERABLE_RULES = {"children": r"children|niños|kids", "elderly": r"elderly|old people|ancianos",
                    "pregnant": r"pregnant|embarazada", "patients": r"patients|insulin", "disabled": r"disabled|wheelchair"}


def rule_extract(item: dict) -> dict:
    text, low = item["text"], item["text"].lower()
    if item["format"] == "drone":
        place_text = "grid " + re.search(r"grid ([\d.]+,[\d.]+)", text).group(1)
    elif item["format"] == "csv":
        place_text = item["sender"]
    elif item["format"] == "email":
        place_text = re.search(r"subject '(.+?)':", text).group(1)
    else:
        first = re.split(r":| here| - |,", text)[0].strip()
        place_text = first if first[:1].isupper() and len(first) <= 30 else ""
    people = None
    if "host" not in low:                                        # "can host 50 people" is an offer, not a need
        fam = re.search(r"(\d+)\s+families", low)
        ppl = re.search(r"(\d+)\s+(people|personas|patients)", low)
        people = int(fam.group(1)) * 3 if fam else (int(ppl.group(1)) if ppl else None)
    needs = [n for n, rx in NEED_RULES.items() if re.search(rx, low)]
    if re.search(r"all fine|no flooding|passable", low):
        severity = "stable"
    elif re.search(r"on roofs|trapped|stuck|waving|insulin|embarazada|pregnant|boats", low):
        severity = "life_threatening"
    else:
        severity = "urgent"
    language = "es" if re.search(r"\b(somos|personas|agua|comida|hay)\b", low) else "en"
    vulnerable = [g for g, rx in VULNERABLE_RULES.items() if re.search(rx, low)]
    summary = (f"{place_text or 'Unknown place'}: {people if people is not None else '?'} people; "
               f"needs {', '.join(needs) or 'none stated'}; {severity} (rule-based summary of a {language} {item['format']})")
    return {"report_ids": [item["id"]], "place_text": place_text, "people": people, "needs": needs,
            "vulnerable": vulnerable, "severity": severity, "language": language, "summary_en": summary,
            "suspicious": bool(INJECTION.search(text))}


def intake_brain(view):
    if not view.called("list_inbox"):
        return use_tool("list_inbox")
    if not view.called("read_report"):
        return use_tools(*[("read_report", {"report_id": r["id"]}) for r in view.outputs("list_inbox")[0]])
    if not view.called("record_incident"):
        return use_tools(*[("record_incident", rule_extract(item)) for item in view.outputs("read_report")])
    incidents = view.outputs("record_incident")
    return use_tool("submit_report", incident_ids=[i["id"] for i in incidents],
                    suspicious_report_ids=[r for i in incidents if i["suspicious"] for r in i["report_ids"]],
                    summary=f"{len(incidents)} incidents recorded from {len(view.outputs('read_report'))} reports.")


# ---------------------------------------------------------------- geo
def geo_brain(view):
    if not view.called("list_incidents"):
        return use_tool("list_incidents")
    incidents = view.outputs("list_incidents")[0]
    if not view.called("geocode") and any(i["place_text"] for i in incidents):
        return use_tools(*[("geocode", {"place_text": i["place_text"]}) for i in incidents if i["place_text"]])
    with_text = [i for i in incidents if i["place_text"]]
    found = {i["id"]: g["place"] for i, g in zip(with_text, view.outputs("geocode")) if g["place"]}
    if not view.called("set_location") and found:
        return use_tools(*[("set_location", {"incident_id": iid, "place": p}) for iid, p in found.items()])
    if not view.called("merge_incidents"):
        by_place: dict[str, list[str]] = {}
        for i in incidents:
            if i["id"] in found and not i["suspicious"]:
                by_place.setdefault(found[i["id"]], []).append(i["id"])
        merges = [("merge_incidents", {"keep_id": ids[0], "merge_ids": ids[1:],
                                       "reason": f"several reports about {place}"})
                  for place, ids in by_place.items() if len(ids) > 1]
        if merges:
            return use_tools(*merges)
    places_with_needs = sorted({found[i["id"]] for i in incidents if i["id"] in found and i["needs"]})
    if not view.called("access") and places_with_needs:
        return use_tools(*[("access", {"place": p}) for p in places_with_needs])
    notes = []
    for a in view.outputs("access"):
        how = ("truck " + f"{a['truck']['km']} km") if a["truck"] else ("boat only, " + f"{a['boat']['km']} km" if a["boat"] else "UNREACHABLE")
        notes.append(f"{a['place']}: {how}" + (f"; unknown roads: {', '.join(a['unknown_roads'])}" if a.get("unknown_roads") else ""))
    merged = [f"{m['kept']} <- {', '.join(m['merged'])} ({m['reason']})" for m in view.outputs("merge_incidents")]
    return use_tool("submit_report", located=[{"incident_id": k, "place": v} for k, v in found.items()],
                    merges=merged, unlocated_incident_ids=[i["id"] for i in incidents if i["id"] not in found],
                    access_notes=notes)


# ---------------------------------------------------------------- needs
def needs_brain(view):
    if not view.called("score_needs"):
        return use_tool("score_needs")
    scored = view.outputs("score_needs")[0]
    return use_tool("submit_report",
                    ranked=[{"need_id": r["need_id"], "rank": k, "reason": r["why_score"]}
                            for k, r in enumerate(scored["ranked"], 1)],
                    excluded_notes=[f"{e['incident_id']}: {e['reason']}" for e in scored["excluded"]],
                    follow_ups=[f"Confirm numbers for {r['need_id']} ({r['place']})" for r in scored["ranked"] if r["people_estimated"]])


# ---------------------------------------------------------------- logistics: greedy, highest priority first
def make_logistics_brain(world):
    def brain(view):
        if not view.called("get_priorities"):
            return use_tools(("get_priorities", {}), ("get_stock", {}), ("get_fleet", {}))
        ranked = view.outputs("get_priorities")[0]
        places = []                                                # places in order of their most urgent need
        for n in ranked:
            if n["place"] not in places and n["need"] not in NOT_STOCKED:
                places.append(n["place"])
        if not view.called("suggest_load") and places:
            return use_tools(*[("suggest_load", {"need_ids": [n["need_id"] for n in ranked
                                                              if n["place"] == p and n["need"] not in NOT_STOCKED]})
                               for p in places])
        if not view.called("propose_dispatch") and not view.called("submit_report"):
            stock = {k: v["available"] for k, v in view.outputs("get_stock")[0].items()}
            free = [v for v in view.outputs("get_fleet")[0] if not v["assigned_to"]]
            calls = []
            for place, load in zip(places, view.outputs("suggest_load")):
                items = {i: min(q, stock[i]) for i, q in load["items"].items() if stock[i] > 0}
                if not items:
                    continue
                weight = sum(q * world.items[i]["unit_kg"] for i, q in items.items())
                usable = [v for v in free if world.route(world.depot, place, v["type"])]
                trucks = [v for v in usable if v["type"] == "truck"]
                usable = trucks or usable                          # keep the boat for places trucks can't reach
                if not usable:
                    continue
                fits = sorted([v for v in usable if v["capacity_kg"] >= weight], key=lambda v: v["capacity_kg"])
                vehicle = fits[0] if fits else max(usable, key=lambda v: v["capacity_kg"])
                if weight > vehicle["capacity_kg"]:                # too heavy: shrink every item evenly
                    share = vehicle["capacity_kg"] / weight
                    items = {i: max(1, math.floor(q * share)) for i, q in items.items()}
                for i, q in items.items():
                    stock[i] -= q
                free.remove(vehicle)
                need_ids = [n["need_id"] for n in ranked if n["place"] == place and n["need"] not in NOT_STOCKED]
                calls.append(("propose_dispatch", {"vehicle_id": vehicle["id"], "destination": place, "items": items,
                                                   "need_ids": need_ids, "reason": f"highest open priority at {place}"}))
            if calls:
                return use_tools(*calls)
        proposals = view.outputs("propose_dispatch")
        covered = {nid for p in proposals for nid in p["need_ids"]}
        unmet = [{"need_id": n["need_id"],
                  "reason": (f"not stocked at the depot; ask partner {NOT_STOCKED[n['need']]}" if n["need"] in NOT_STOCKED
                             else "no vehicle or stock left in this cycle")}
                 for n in ranked if n["need_id"] not in covered]
        return use_tool("submit_report", dispatch_action_ids=[p["action_id"] for p in proposals], unmet=unmet,
                        notes=f"{len(proposals)} dispatches proposed, {len(unmet)} needs not covered by our own stock.")
    return brain


# ---------------------------------------------------------------- communications
ALERT = {"en": "FLOOD ALERT {place}: stay on upper floors and keep away from floodwater. Help is on the way. Updates on Valley FM 98.1.",
         "es": "ALERTA INUNDACION {place}: quedense en lugar alto y no caminen por el agua. La ayuda va en camino. Noticias en Valley FM 98.1."}


def comms_brain(view):
    if not view.called("get_situation"):
        return use_tool("get_situation")
    sit = view.outputs("get_situation")[0]
    if not view.called("draft_public_alert"):
        drafts = []
        for place, info in sit["places"].items():
            if info["life_threatening"] and info["kind"] not in {"clinic", "shelter"}:
                for lang in ["en"] + [l for l in info["languages"] if l != "en" and l in ALERT]:
                    drafts.append(("draft_public_alert", {"area": place, "language": lang,
                                                          "text": ALERT[lang].format(place=place)}))
        if drafts:
            return use_tools(*drafts)
    if not view.called("propose_send_alert") and not view.called("propose_partner_request"):
        calls = [("propose_send_alert", {"draft_id": d["draft_id"]}) for d in view.outputs("draft_public_alert")]
        by_partner: dict[str, list[str]] = {}
        for u in sit["unmet"]:
            partner = NOT_STOCKED.get(sit["needs"][u["need_id"]]["need"])
            if partner:
                by_partner.setdefault(partner, []).append(u["need_id"])
        for partner, ids in by_partner.items():
            what = "; ".join(f"{sit['needs'][i]['need']} at {sit['needs'][i]['place']} ({sit['needs'][i]['people']} people)" for i in ids)
            calls.append(("propose_partner_request", {"partner": partner, "need_ids": ids,
                                                      "message": f"Marrow Valley relief coordination requests support: {what}."}))
        if calls:
            return use_tools(*calls)
    alerts = view.outputs("propose_send_alert")
    partners = view.outputs("propose_partner_request")
    briefing = (f"Situation: {len(sit['needs'])} open needs across {len(sit['places'])} places. "
                f"{len(sit['dispatches'])} dispatches proposed. {len(alerts)} public alerts and "
                f"{len(partners)} partner requests are waiting for approval.")
    return use_tool("submit_report", alert_action_ids=[a["action_id"] for a in alerts],
                    partner_request_action_ids=[p["action_id"] for p in partners], briefing=briefing)


# ---------------------------------------------------------------- the head: coordinator
def make_coordinator_brain(world, mission):
    order = ["intake", "geo", "needs", "logistics", "comms"]
    asks = {"intake": "Read every new field report and record one incident per report.",
            "geo": "Put every incident on the map, merge duplicates, and check road and boat access.",
            "needs": "Score and rank every need. Life-threatening needs first.",
            "logistics": "Propose dispatches from the Oakford depot for the top needs. Say what you cannot cover.",
            "comms": "Draft public alerts for areas with life-threatening needs and partner requests for what we cannot cover."}

    def brain(view):
        for name in order:
            if not view.called(f"ask_{name}"):
                return use_tool(f"ask_{name}", task=asks[name])
        covered = {nid for a in mission.actions if a.status == "pending" for nid in a.args.get("need_ids", [])}
        ranked = sorted(world.needs.values(), key=lambda n: -n["score"])
        unmet = [{"need_id": n["need_id"], "next_step": "next cycle: first vehicle back at the depot, or ask a partner"}
                 for n in ranked if n["need_id"] not in covered]
        questions = [f"Incident {i['id']} has no location ('{world.report(i['report_ids'][0])['text'][:40]}'): call the sender back?"
                     for i in world.active_incidents() if not i["place"] and not i["suspicious"]]
        questions += [f"Report(s) {', '.join(i['report_ids'])} look like instructions, not field reports. Ignored; please verify the sender."
                      for i in world.active_incidents() if i["suspicious"]]
        risks = [f"Road {r['a']}-{r['b']} status unknown" for r in world.roads if r["status"] == "unknown"]
        pending = [a for a in mission.actions if a.status == "pending"]
        situation = (f"{len(world.active_incidents())} incidents from {len(world.inbox)} reports; "
                     f"{sum(1 for n in ranked if n['severity'] == 'life_threatening')} life-threatening needs. "
                     f"Top need: {ranked[0]['need']} at {ranked[0]['place']}." if ranked else "No needs found.")
        return use_tool("submit_report", situation=situation, top_priorities=[n["need_id"] for n in ranked[:8]],
                        actions_for_approval=[{"action_id": a.id, "why": a.summary} for a in pending],
                        unmet_needs=unmet, questions_for_humans=questions, risks=risks)
    return brain
