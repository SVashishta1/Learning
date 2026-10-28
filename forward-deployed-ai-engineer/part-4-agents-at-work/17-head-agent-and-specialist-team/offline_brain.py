"""offline_brain.py: scripted stand-ins for every agent, so team.py runs free with --offline.

This is NOT AI. Each role follows a fixed script of tool calls (the same ones a good model would make), reads the
REAL tool results, and writes its report from those numbers. The head's script reads FACTS that the specialists'
scripts noted down. Use it to see the orchestration, budgets and message formats; use a real model for real reasoning.
"""
import json
import re
import threading

from fake_llm import json_reply, text_reply, tool_calls_reply

FACTS: dict = {}                      # numbers the scripted specialists found, for the scripted head
_lock = threading.Lock()

SPLIT_SQL = ("SELECT CASE WHEN collected_date <= '2026-09-07' THEN 'week 1 (1-7 Sep)' ELSE 'weeks 2-4 (8-30 Sep)' END "
             "AS period, SUM(on_time = 0) AS late, SUM(on_time = 0 AND dispatched_date > collected_date) AS late_hub_dispatch, "
             "SUM(on_time = 0 AND dispatched_date = collected_date AND carrier = 'SwiftHaul') AS late_swifthaul_transit, "
             "SUM(on_time = 0 AND dispatched_date = collected_date AND carrier <> 'SwiftHaul') AS late_other "
             "FROM shipments WHERE collected_date LIKE '2026-09%' GROUP BY 1 ORDER BY 1")
SCRIPTS = {   # (role, task kind) -> list of turns; each turn = list of (tool, args)
    ("data_analyst", "T"): [
        [("describe_tables", {})],
        [("run_sql", {"query": "SELECT substr(collected_date, 1, 7) AS month, COUNT(*) AS shipments, "
                               "ROUND(100.0 * AVG(on_time), 1) AS on_time_pct FROM shipments GROUP BY 1 ORDER BY 1"})],
        [("run_sql", {"query": "SELECT substr(collected_date, 1, 7) AS month, carrier, COUNT(*) AS shipments, "
                               "ROUND(100.0 * AVG(on_time), 1) AS on_time_pct FROM shipments GROUP BY 1, 2 ORDER BY 2, 1"})]],
    ("data_analyst", "F"): [[("run_sql", {"query": SPLIT_SQL})]],
    ("operations", "T"): [
        [("carrier_scorecard", {"month": "2026-08"}), ("carrier_scorecard", {"month": "2026-09"})],
        [("search_ops_notes", {"month": "2026-09"})]],
    ("customer_voice", "T"): [
        [("ticket_stats", {"month": "2026-08"}), ("ticket_stats", {"month": "2026-09"})],
        [("sample_tickets", {"month": "2026-09", "keyword": "SwiftHaul", "limit": 2}),
         ("sample_tickets", {"month": "2026-09", "keyword": "tracking", "limit": 2})]],
    ("contracts", "T"): [
        [("search_documents", {"query": "SwiftHaul service level credits recovery plan"})],
        [("search_documents", {"query": "customer compensation late Express proactive contact"})]],
    ("contracts", "F"): [[("calculate_service_credit", {"on_time_percent": 54.0, "invoice_gbp": 48000})]],
}


def _role(system: str) -> str:
    for marker, role in (("head of Northwind", "head"), ("data analyst", "data_analyst"),
                         ("operations specialist", "operations"), ("customer-voice", "customer_voice"),
                         ("contracts and policy", "contracts")):
        if marker in system:
            return role
    raise ValueError("unknown role")


def _tool_results(messages) -> list:
    """Every tool result in the conversation so far, parsed from JSON where possible."""
    out = []
    for m in messages:
        if m["role"] == "user" and isinstance(m["content"], list):
            for block in m["content"]:
                if block.get("type") == "tool_result":
                    try:
                        out.append(json.loads(block["content"]))
                    except (json.JSONDecodeError, TypeError):
                        out.append(block["content"])
    return out


def _finding(claim, evidence, confidence="high"):
    return {"claim": claim, "evidence": evidence, "confidence": confidence}


def _specialist_report(role: str, kind: str, results: list) -> dict:
    if role == "data_analyst" and kind == "T":
        months, carriers = results[1], results[2]
        by = {(r["carrier"], r["month"]): r["on_time_pct"] for r in carriers}
        drops = sorted({c for c, _ in by}, key=lambda c: by[(c, "2026-09")] - by[(c, "2026-08")])
        worst = drops[0]
        with _lock:
            FACTS.update(aug=months[0]["on_time_pct"], sep=months[1]["on_time_pct"], worst=worst,
                         worst_aug=by[(worst, "2026-08")], worst_sep=by[(worst, "2026-09")])
        return {"status": "complete",
                "summary": f"On-time fell from {months[0]['on_time_pct']}% to {months[1]['on_time_pct']}%. "
                           f"{worst} collapsed from {by[(worst, '2026-08')]}% to {by[(worst, '2026-09')]}%; "
                           "the other carriers moved by a few points at most. The main cause is the carrier.",
                "findings": [_finding(f"Overall on-time: {months[0]['on_time_pct']}% in August, {months[1]['on_time_pct']}% "
                                      f"in September ({months[1]['shipments']} shipments).", "run_sql: on-time by month"),
                             _finding(f"{worst}: {by[(worst, '2026-08')]}% -> {by[(worst, '2026-09')]}%.", "run_sql: on-time by carrier and month"),
                             _finding("Parcelink, CoastExpress and ScotFreight stayed above 93%.", "run_sql: on-time by carrier and month", "medium")],
                "recommendations": [f"Focus on {worst}'s North region lanes."],
                "open_questions": ["Is any of the drop caused by hubs rather than carriers?"]}
    if role == "data_analyst":
        rows = results[0]
        late = sum(r["late"] for r in rows)
        hub = sum(r["late_hub_dispatch"] for r in rows)
        swift = sum(r["late_swifthaul_transit"] for r in rows)
        other = sum(r["late_other"] for r in rows)
        wk1 = next(r for r in rows if r["period"].startswith("week 1"))
        with _lock:
            FACTS.update(late=late, hub=hub, swift=swift, other=other, wk1_hub=wk1["late_hub_dispatch"])
        return {"status": "complete",
                "summary": f"Both happened, at different times. Of {late} late September shipments, {hub} were dispatched "
                           f"late by a hub ({wk1['late_hub_dispatch']} of them in week 1), {swift} were SwiftHaul transit "
                           f"delays, and {other} were normal background lateness.",
                "findings": [_finding(f"Hub dispatch delays: {hub} of {late} late shipments ({100 * hub // late}%), "
                                      f"{wk1['late_hub_dispatch']} in 1-7 Sep.", "run_sql: late September split by week and cause"),
                             _finding(f"SwiftHaul transit delays: {swift} of {late} ({100 * swift // late}%), almost all from 8 Sep.",
                                      "run_sql: late September split by week and cause"),
                             _finding(f"Other lateness: {other} of {late} ({100 * other // late}%), similar to August's level.",
                                      "run_sql: late September split by week and cause", "medium")],
                "recommendations": ["Treat the hub and the carrier as two separate incidents."], "open_questions": []}
    if role == "operations":
        aug, sep, notes = results
        leeds = sum(r["late_dispatches"] for r in sep if r["hub"] == "Leeds")
        swift = next(r for r in sep if r["carrier"] == "SwiftHaul")
        return {"status": "complete",
                "summary": f"The September problems started at the Leeds hub: the new warehouse system went live on 1 Sep "
                           f"and caused {leeds} late dispatches. SwiftHaul also reported a driver shortage from 9 Sep. "
                           "We think the Leeds hub cutover was the main cause.",
                "findings": [_finding(f"Leeds hub: {leeds} late dispatches in September (0 in August).", "carrier_scorecard 2026-08 / 2026-09"),
                             _finding("Leeds WMS cutover 1 Sep; backlog of ~600 parcels on 2 Sep, cleared on 8 Sep.", "ops_notes 2, 5, 8 Sep"),
                             _finding(f"SwiftHaul driver shortage at Wakefield from 9 Sep; SwiftHaul on-time {swift['on_time_pct']}% in September.",
                                      "ops_notes 9, 16 Sep; carrier_scorecard", "medium"),
                             _finding("No written recovery plan from SwiftHaul as of 29 Sep.", "ops_notes 29 Sep")],
                "recommendations": ["Add rollback criteria and extra staff to future hub system cutovers.",
                                    "Move some North volume away from SwiftHaul until it recovers."],
                "open_questions": ["How much of the drop is the hub versus SwiftHaul?"]}
    if role == "customer_voice":
        aug, sep, swift, tracking = results
        late_aug = next((r["tickets"] for r in aug if r["category"] == "late_delivery"), 0)
        late_sep = next((r["tickets"] for r in sep if r["category"] == "late_delivery"), 0)
        return {"status": "complete",
                "summary": f"Late-delivery tickets rose from {late_aug} in August to {late_sep} in September. Customers "
                           "mention SwiftHaul drivers not turning up and tracking that stops after Leeds.",
                "findings": [_finding(f"Late-delivery tickets: {late_aug} (Aug) -> {late_sep} (Sep).", "ticket_stats"),
                             _finding(f"{swift['matching_tickets']} September tickets name SwiftHaul, e.g. \"{swift['examples'][0]['text']}\"",
                                      "sample_tickets keyword=SwiftHaul"),
                             _finding(f"{tracking['matching_tickets']} mention tracking, e.g. \"{tracking['examples'][0]['text']}\"",
                                      "sample_tickets keyword=tracking", "medium")],
                "recommendations": ["Send a proactive apology to affected customers.", "Fix tracking updates for delayed parcels."],
                "open_questions": []}
    if role == "contracts" and kind == "T":
        return {"status": "complete",
                "summary": "SwiftHaul owes 5% of the monthly invoice per point below 95% (capped at 25%) and must send a "
                           "recovery plan within 10 working days if below 90%. Late Express parcels get the £4.50 surcharge back.",
                "findings": [_finding("SLA 95%; credit 5% of invoice per full point below, max 25%; September invoice £48,000.", "swifthaul-contract.md"),
                             _finding("Below 90%: written recovery plan within 10 working days; 2 months below 90% allow moving 50% of volume.", "swifthaul-contract.md"),
                             _finding("Incidents affecting 50+ parcels need a proactive apology within 2 working days.", "customer-compensation-policy.md")],
                "recommendations": ["Claim the service credit in writing within 30 days of month end."],
                "open_questions": ["What was SwiftHaul's September on-time %? Needed to compute the credit."]}
    credit = results[0]
    with _lock:
        FACTS.update(credit=credit["credit_gbp"], credit_rate=credit["credit_rate"])
    return {"status": "complete", "summary": f"SwiftHaul owes £{credit['credit_gbp']:,.0f} for September "
                                             f"({credit['points_below_95']} points below 95%, capped at {credit['credit_rate']:.0%}).",
            "findings": [_finding(f"Service credit: £{credit['credit_gbp']:,.0f} ({credit['credit_rate']:.0%} of £48,000).", "calculate_service_credit")],
            "recommendations": ["Claim it in writing before 30 October."], "open_questions": []}


def _head(schema: str, request: dict):
    if schema == "Plan":
        FACTS.clear()                                      # a new run starts with an empty notebook
        return json_reply({"goal": "Explain the September on-time drop and recommend actions", "tasks": [
            {"specialist": "data_analyst", "question": "How did on-time % change from August to September, overall and per carrier?", "why": "size and location of the drop"},
            {"specialist": "operations", "question": "What happened at our hubs and carriers in September?", "why": "events on the ground"},
            {"specialist": "customer_voice", "question": "How did late-delivery complaints change and what do customers say?", "why": "customer impact"},
            {"specialist": "contracts", "question": "What do the carrier contracts and our compensation policy say about this?", "why": "what we are owed and owe"}]})
    if schema == "Review":
        if "worst_sep" not in FACTS:                       # the analyst never reported: nothing to compare
            return json_reply({"follow_ups": []})
        return json_reply({"follow_ups": [
            {"kind": "conflict", "topic": "main cause", "between": ["data_analyst", "operations"],
             "description": "The analyst blames SwiftHaul; operations blames the Leeds hub cutover.", "ask": "data_analyst",
             "question": "Split September's late shipments by week (1-7 Sep vs 8-30 Sep) and by cause: late hub dispatch "
                         "(dispatched_date > collected_date) vs SwiftHaul transit vs other."},
            {"kind": "gap", "topic": "service credit amount", "between": ["contracts", "data_analyst"],
             "description": "Contracts needs SwiftHaul's September on-time %.", "ask": "contracts",
             "question": f"SwiftHaul's September on-time was {FACTS['worst_sep']}% and the invoice is £48,000. Compute the service credit."}]})
    f = FACTS
    if "late" not in f or "credit" not in f:               # specialists stopped early (budget): say so honestly
        return json_reply({"answer": "The team ran out of budget before the analysis was complete, so there is no "
                                     "reliable answer yet. No numbers are reported rather than guessed.",
                           "root_causes": [], "actions": [], "disagreements_resolved": [],
                           "open_questions": ["Re-run with a bigger budget (--max-calls / --max-usd)."]})
    pct = lambda n: f"about {round(100 * n / f['late'])}% ({n} of {f['late']} late shipments)"
    return json_reply({
        "answer": f"On-time delivery fell from {f['aug']}% in August to {f['sep']}% in September because of two separate "
                  f"incidents: the Leeds hub's warehouse-system cutover delayed dispatches in the first week, and from 8 "
                  f"September a driver shortage at SwiftHaul cut its on-time rate to {f['worst_sep']}%. SwiftHaul is the "
                  "larger and still-running problem; the hub issue is over but showed a planning gap.",
        "root_causes": [
            {"cause": "SwiftHaul driver shortage (North region, from 8 Sep)", "evidence": "analyst split query; ops notes 9/16/29 Sep; tickets naming SwiftHaul",
             "share_of_late_shipments": pct(f["swift"]), "confidence": "high"},
            {"cause": "Leeds hub WMS cutover (1-7 Sep)", "evidence": "late dispatches in scorecard; ops notes 2-8 Sep; analyst split query",
             "share_of_late_shipments": pct(f["hub"]), "confidence": "high"},
            {"cause": "Normal background lateness", "evidence": "analyst split query; similar to August",
             "share_of_late_shipments": pct(f["other"]), "confidence": "medium"}],
        "actions": [
            {"action": f"Claim SwiftHaul's September service credit of £{f['credit']:,.0f} in writing before 30 October",
             "owner": "Carrier manager", "expected_impact": "recovers part of the cost", "needs_human_approval": True},
            {"action": "Formally request SwiftHaul's recovery plan (due within 10 working days under the contract)",
             "owner": "Carrier manager", "expected_impact": "a dated plan to return above 95%", "needs_human_approval": True},
            {"action": "Move about 30% of North volume to Parcelink until SwiftHaul is above 90% for 4 weeks",
             "owner": "Operations director", "expected_impact": "fewer late North parcels within a week", "needs_human_approval": True},
            {"action": "Send the proactive apology and refund Express surcharges for late September parcels",
             "owner": "Head of Customer Service", "expected_impact": "fewer repeat complaints", "needs_human_approval": True},
            {"action": "Add rollback criteria, extra first-week staff and customer notice to future hub system cutovers",
             "owner": "Leeds hub manager", "expected_impact": "prevents a repeat", "needs_human_approval": False}],
        "disagreements_resolved": [f"Analyst (SwiftHaul) vs operations (Leeds hub): both were right for different weeks. "
                                   f"The split shows {f['wk1_hub']} late hub dispatches in 1-7 Sep and {f['swift']} SwiftHaul "
                                   "transit delays, almost all after 8 Sep."],
        "open_questions": ["Is SwiftHaul's 'mid-October' recovery realistic? Check October's first two weeks.",
                           "Did the Leeds cutover also delay tracking updates (customers mention frozen tracking)?"]})


def respond(request: dict):
    system = request["system"][0]["text"]
    role = _role(system)
    fmt = request.get("output_config", {}).get("format")
    schema = fmt["schema"].get("title") if fmt else None
    if role == "head":
        return _head(schema, request)
    task = json.loads(request["messages"][0]["content"])
    kind = task["task_id"][0]                               # T = first round, F = follow-up
    if schema == "Report":
        return json_reply(_specialist_report(role, kind, _tool_results(request["messages"])))
    turn = sum(m["role"] == "assistant" for m in request["messages"])
    script = SCRIPTS[(role, kind)]
    if turn < len(script):
        return tool_calls_reply([(name, args, f"{task['task_id']}-{turn}-{i}") for i, (name, args) in enumerate(script[turn])])
    return text_reply("I have what I need for my report.")
