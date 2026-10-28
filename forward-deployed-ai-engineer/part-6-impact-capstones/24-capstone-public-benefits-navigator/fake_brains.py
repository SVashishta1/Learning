"""fake_brains.py: rule-based stand-ins for the model, used when FAKE_LLM=1 (tests, CI, demos without a key).

They call the same tools as a real model would. The intake rules understand a few English and Spanish
phrasings only; a real (or local) model understands far more. You can skip this file on a first read.
"""
import re

from llm import use_tool, use_tools

PROGRAMME_IDS = ["foodbridge", "kidcare", "warmhome", "rentrelief", "schoolmeals", "childcare"]


def _num(s: str) -> float:
    """'1,450' -> 1450, '2.400' (Spanish thousands) -> 2400, '600' -> 600"""
    s = re.sub(r"[.,](?=\d{3}\b)", "", s)
    return float(s.replace(",", "."))


AMOUNT = r"(\d{1,3}(?:[.,]\d{3})+|\d+)"


def parse_story(text: str) -> dict:
    low = text.lower()
    spanish = bool(re.search(r"\b(somos|hijos?|ganamos|al mes|renta|vivo|me llamo)\b", low))
    child_ages = []
    for m in re.finditer(r"(?:aged|ages|de)\s+(\d+)(?:\s*(?:,|and|y)\s*(\d+))?", low):
        child_ages += [int(g) for g in m.groups() if g]
    for m in re.finditer(r"my (?:son|daughter|child)(?: \[name_\d\]| \w+)? is (\d+)", low):
        child_ages.append(int(m.group(1)))
    size = None
    m = re.search(r"(?:we are|somos|family of|there are)\s+(?:a family of\s+)?(\d+)", low)
    if m:
        size = int(m.group(1))
    elif re.search(r"live alone|vivo solo|vivo sola", low):
        size = 1
    if re.search(r"my (?:husband|wife|partner)|mi (?:esposo|esposa|pareja)", low):
        adults = 2
    else:
        adults = 1
    size = size or adults + len(child_ages)
    works = None
    if re.search(r"unemployed|retired|jubilad|desemplead", low):
        works = False
    elif re.search(r"\bwork|part-time|full-time|study|studies|trabaj|estudi", low):
        works = True
    members = [{"role": "adult", "age": None, "works_or_studies": works} for _ in range(max(0, size - len(child_ages)))]
    members += [{"role": "child", "age": a} for a in child_ages]
    income = None
    m = re.search(AMOUNT + r"\s*(?:euros?\s*)?(a|per|al|a la)\s*(month|week|year|mes|semana|año)", low)
    if m:
        amount, period = _num(m.group(1)), m.group(3)
        income = round(amount * {"week": 52 / 12, "semana": 52 / 12, "year": 1 / 12, "año": 1 / 12}.get(period, 1), 2)
    rent = None
    if re.search(r"own our home|own my home|no rent|sin renta|casa propia", low):
        rent = 0.0
    else:
        m = re.search(r"rent (?:is )?" + AMOUNT, low) or re.search(AMOUNT + r"\s*(?:de |in |for )?(?:rent|renta)", low)
        if m:
            rent = _num(m.group(1))
    heating = None
    if re.search(r"heating is included|included in (?:my|the) rent|no heating bill", low):
        heating = False
    elif re.search(r"heating|energy bill|gas bill|calefacci", low):
        heating = True
    return {"household_size": size, "members": members, "monthly_income": income, "monthly_rent": rent,
            "pays_heating": heating, "county_resident": True if "brightwater" in low else None,
            "eviction_notice": True if re.search(r"eviction|desalojo", low) else None,
            "preferred_language": "es" if spanish else "en"}


def intake_brain(view):
    if not view.called("get_story"):
        return use_tool("get_story")
    if not view.called("save_profile") or view.last_error():
        if view.called("save_profile"):                       # the tool rejected our profile: give up politely
            return use_tool("submit_report", missing_info=["could not build a valid profile"], preferred_language="en",
                            summary="Intake failed; a caseworker should talk to the family.")
        return use_tool("save_profile", **parse_story(view.outputs("get_story")[0]["story"]))
    p = view.outputs("save_profile")[0]["profile"]
    missing = [k for k in ("monthly_income", "monthly_rent", "pays_heating", "county_resident") if p[k] is None]
    return use_tool("submit_report", missing_info=missing, preferred_language=p["preferred_language"],
                    summary=f"Household of {p['household_size']}, income {p['monthly_income']} a month.")


def eligibility_brain(view):
    if not view.called("check_rules"):
        return use_tools(*[("check_rules", {"programme": p}) for p in PROGRAMME_IDS])
    results = view.outputs("check_rules")
    if not view.called("search_policies"):
        return use_tools(*[("search_policies", {"query": f"{r['name']} who can get it income limit", "programme": r["programme"]})
                           for r in results])
    findings = []
    for r, hits in zip(results, view.outputs("search_policies")):
        reasons = [f"{c['criterion']}: {c['result']} ({c['detail']})" for c in r["criteria"]]
        findings.append({"programme": r["programme"], "status": r["status"], "reasons": reasons,
                         "citations": sorted({c["source"] for c in r["criteria"]} | {hits[0]["chunk_id"]} if hits else
                                             {c["source"] for c in r["criteria"]})})
    return use_tool("submit_report", findings=findings)


def documents_brain(view):
    if not view.called("get_findings"):
        return use_tool("get_findings")
    f = view.outputs("get_findings")[0]
    progs = f["likely"] + f["maybe"]
    if not progs:
        return use_tool("submit_report", checklist=[])
    if not view.called("documents_for"):
        return use_tool("documents_for", programmes=progs)
    docs = view.outputs("documents_for")[0]
    return use_tool("submit_report", checklist=[
        {"document": d["document"], "label": d["label"], "for_programmes": d["for"],
         "tip": f"One copy covers {len(d['for'])} applications." if len(d["for"]) > 1 else ""} for d in docs])


def forms_brain(view):
    if not view.called("get_findings"):
        return use_tools(("get_findings", {}), ("get_profile", {}))
    progs = view.outputs("get_findings")[0]["likely"]
    if progs and not view.called("get_form"):
        return use_tools(*[("get_form", {"programme": p}) for p in progs])
    if progs and not view.called("fill_form"):
        prof = view.outputs("get_profile")[0]
        tok = prof["placeholders"]
        values_from = {"applicant_name": prof["applicant"] or (tok.get("NAME") or [""])[0], "address": (tok.get("ADDRESS") or [""])[0],
                       "phone": (tok.get("PHONE") or [""])[0], "household_size": str(prof["profile"]["household_size"]),
                       "monthly_income": str(prof["profile"]["monthly_income"] or ""),
                       "monthly_rent": str(prof["profile"]["monthly_rent"] if prof["profile"]["monthly_rent"] is not None else ""),
                       "children_ages": ", ".join(str(m["age"]) for m in prof["profile"]["members"] if m["role"] == "child")}
        calls = []
        for form in view.outputs("get_form"):
            values = {f["field"]: values_from.get(f["field"], "") for f in form["fields"]}
            calls.append(("fill_form", {"programme": form["programme"], "values": {k: v for k, v in values.items() if v}}))
        return use_tools(*calls)
    filled = view.outputs("fill_form")
    ready = [f["programme"] for f in filled if not f["missing"]]
    if ready and not view.called("propose_submit"):
        return use_tools(*[("propose_submit", {"programme": p}) for p in ready])
    return use_tool("submit_report", drafted=[f["programme"] for f in filled],
                    submit_action_ids=[a["action_id"] for a in view.outputs("propose_submit")],
                    missing_fields={f["programme"]: f["missing"] for f in filled if f["missing"]})


TEMPLATES = {
    "en": ("Good news. You may be able to get: {likely}. ", "We did not find a programme you are likely to get today. ",
           "You might also get: {maybe}. We need a few more facts to know. ", "Bring these papers: {docs}. ",
           "A county caseworker makes the final decision. This is not a decision."),
    "es": ("Buenas noticias. Es posible que pueda recibir: {likely}. ", "Hoy no encontramos un programa que probablemente pueda recibir. ",
           "Tal vez también: {maybe}. Necesitamos algunos datos más. ", "Traiga estos papeles: {docs}. ",
           "Un trabajador social del condado toma la decisión final. Esto no es una decisión."),
}


def explainer_brain(view):
    if not view.called("get_findings"):
        return use_tools(("get_findings", {}), ("get_checklist", {}))
    f, docs = view.outputs("get_findings")[0], view.outputs("get_checklist")[0]
    lang = f["language"] if f["language"] in TEMPLATES else "en"
    yes, no, maybe, papers, end = TEMPLATES[lang]
    names = f["names"]
    text = (yes.format(likely=", ".join(names[p] for p in f["likely"])) if f["likely"] else no)
    text += maybe.format(maybe=", ".join(names[p] for p in f["maybe"])) if f["maybe"] else ""
    text += papers.format(docs="; ".join(d["label"].split(" (")[0][0].lower() + d["label"].split(" (")[0][1:] for d in docs)) if docs else ""
    text += end
    if not view.called("save_explanation"):
        return use_tool("save_explanation", language=lang, text=text)
    saved = view.outputs("save_explanation")[0]
    return use_tool("submit_report", language=lang, reading_grade=saved["reading_grade"], explanation=text)


def make_navigator_brain(mission):
    order = [("intake", "Read the family's story and save their household profile."),
             ("eligibility", "Check all six programmes against the rules and the policy text, with citations."),
             ("documents", "Make one combined checklist of papers for the likely and maybe programmes."),
             ("forms", "Pre-fill the forms of likely programmes with placeholders and queue complete ones for approval."),
             ("explainer", "Explain the result in plain words in the family's language.")]

    def brain(view):
        for name, task in order:
            if not view.called(f"ask_{name}"):
                return use_tool(f"ask_{name}", task=task)
        rules = mission.state["rules"]
        by = {s: [p for p, r in rules.items() if r["status"] == s] for s in ("likely", "maybe", "unlikely")}
        forms = (mission.reports.get("forms") or {}).get("report") or {}
        steps = [f"Gather the papers on the checklist ({len((mission.reports.get('documents') or {}).get('report', {}).get('checklist', []))} items)."]
        steps += [f"Ask the family for: {', '.join(v)} ({k} form)" for k, v in (forms.get("missing_fields") or {}).items()]
        if by["maybe"]:
            steps.append(f"Answer the open questions to settle: {', '.join(by['maybe'])}")
        pending = [a.id for a in mission.actions if a.status == "pending"]
        if pending:
            steps.append("Review and approve the form submissions together with the family.")
        return use_tool("submit_report", summary=f"{len(by['likely'])} likely, {len(by['maybe'])} maybe, {len(by['unlikely'])} unlikely.",
                        likely=by["likely"], maybe=by["maybe"], unlikely=by["unlikely"], next_steps=steps,
                        actions_for_approval=pending,
                        disclaimer="This is guidance, not a decision. Only a Brightwater County caseworker decides. "
                                   "The programmes in this project are fictional.")
    return brain
