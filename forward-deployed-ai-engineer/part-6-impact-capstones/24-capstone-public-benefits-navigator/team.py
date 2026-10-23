"""team.py: the benefits navigator. One head agent (the navigator) and five specialists.

    family's story --redact PII--> navigator (head)
        --ask_intake------> intake        builds the household profile (only placeholders, never names)
        --ask_eligibility-> eligibility   RAG over the policy text + the rules engine, with citations
        --ask_documents---> documents     one combined checklist of papers
        --ask_forms-------> forms         pre-fills forms with placeholders; queues complete ones for approval
        --ask_explainer---> explainer     plain words, in the family's language
    navigator -> FamilyPlan -> family + caseworker approve each submission -> code submits (simulated)

Run it:  FAKE_LLM=1 python team.py
All programmes and rules are FICTIONAL (Brightwater County does not exist).
"""
import json
import os
import sys
from typing import Literal

from pydantic import BaseModel, Field

import fake_brains as fb
import llm
from agent_core import Agent, Budget, Mission, NoArgs, Tool, run_mission
from benefits_tools import (PROGRAMMES, PolicyIndex, Profile, check_all, check_rules, documents_for,
                            form_template, reading_grade)
from privacy import Vault, find_leaks, redact

ProgrammeId = Literal[tuple(PROGRAMMES)]
Status = Literal["likely", "maybe", "unlikely"]


# ================================================================ tool inputs
class Programme(BaseModel):
    programme: ProgrammeId


class Search(BaseModel):
    query: str
    programme: ProgrammeId | None = Field(default=None, description="Only search this programme's policy")


class Programmes(BaseModel):
    programmes: list[ProgrammeId]


class FillForm(BaseModel):
    programme: ProgrammeId
    values: dict[str, str] = Field(description="field -> value. Use placeholders like [NAME_1] for personal details.")


class Explanation(BaseModel):
    language: str = Field(description="2-letter code, the family's language")
    text: str


# ================================================================ reports
class IntakeReport(BaseModel):
    missing_info: list[str] = Field(description="Facts we still need to ask the family")
    preferred_language: str
    summary: str


class Finding(BaseModel):
    programme: ProgrammeId
    status: Status
    reasons: list[str]
    citations: list[str] = Field(description="chunk ids from search_policies or check_rules sources")


class EligibilityReport(BaseModel):
    findings: list[Finding]


class DocItem(BaseModel):
    document: str
    label: str
    for_programmes: list[ProgrammeId]
    tip: str = ""


class DocumentsReport(BaseModel):
    checklist: list[DocItem]


class FormsReport(BaseModel):
    drafted: list[ProgrammeId]
    submit_action_ids: list[str]
    missing_fields: dict[str, list[str]]


class ExplainerReport(BaseModel):
    language: str
    reading_grade: float | None
    explanation: str


class FamilyPlan(BaseModel):
    summary: str
    likely: list[ProgrammeId]
    maybe: list[ProgrammeId]
    unlikely: list[ProgrammeId]
    next_steps: list[str]
    actions_for_approval: list[str]
    disclaimer: str = Field(description="Say clearly that this is not a decision and who decides")


# ================================================================ checks: code reviews the agents' reports
def _rules(m: Mission) -> dict:
    if m.state.get("profile") is None:
        raise ValueError("No household profile yet: ask the intake agent first.")
    m.state["rules"] = check_all(m.state["profile"])
    return m.state["rules"]


def check_intake(r: IntakeReport, m: Mission) -> list[str]:
    return [] if m.state.get("profile") else ["You must call save_profile before reporting."]


def check_eligibility(r: EligibilityReport, m: Mission) -> list[str]:
    rules, index_ids, problems = _rules(m), m.state["index"].ids(), []
    seen = {f.programme for f in r.findings}
    if seen != set(PROGRAMMES):
        problems.append(f"Give exactly one finding for every programme. Missing: {sorted(set(PROGRAMMES) - seen)}")
    for f in r.findings:
        if f.status != rules[f.programme]["status"]:
            problems.append(f"{f.programme}: the rules engine says '{rules[f.programme]['status']}', not '{f.status}'. "
                            "Explain the rules result; do not overrule it.")
        bad = [c for c in f.citations if c not in index_ids or not c.startswith(f.programme + "#")]
        if bad or not f.citations:
            problems.append(f"{f.programme}: cite real sections of this programme's policy (bad: {bad or 'none given'})")
    return problems


def check_documents(r: DocumentsReport, m: Mission) -> list[str]:
    rules = m.state["rules"]
    needed = {d["document"] for d in documents_for([p for p, x in rules.items() if x["status"] in ("likely", "maybe")])}
    missing = needed - {d.document for d in r.checklist}
    return [f"Checklist is missing: {sorted(missing)}"] if missing else []


def check_forms(r: FormsReport, m: Mission) -> list[str]:
    known = {a.id for a in m.actions if a.kind == "submit_application"}
    return [f"Unknown action ids: {sorted(set(r.submit_action_ids) - known)}"] if set(r.submit_action_ids) - known else []


def check_explainer(r: ExplainerReport, m: Mission) -> list[str]:
    saved = m.state.get("explanation")
    return [] if saved and saved["text"] == r.explanation else ["Save the explanation with save_explanation first."]


def check_plan(r: FamilyPlan, m: Mission) -> list[str]:
    rules, problems = m.state.get("rules") or {}, []
    for status in ("likely", "maybe", "unlikely"):
        truth = sorted(p for p, x in rules.items() if x["status"] == status)
        if sorted(getattr(r, status)) != truth:
            problems.append(f"'{status}' must be exactly {truth} (from the rules engine)")
    pending = sorted(a.id for a in m.actions if a.status == "pending")
    if sorted(r.actions_for_approval) != pending:
        problems.append(f"List every pending action for approval: {pending}")
    if "caseworker" not in r.disclaimer.lower():
        problems.append("The disclaimer must say that a caseworker makes the decision.")
    return problems


PROMPTS = {
    "intake": """You are the INTAKE helper of a public-benefits navigator. Read the family's story (personal details
are already replaced by placeholders like [NAME_1]; keep them as they are). Build the household profile and save it
with save_profile: everyone who lives together and shares meals, ages, the household's GROSS MONTHLY income
(convert weekly x 52 / 12, yearly / 12), rent (0 if they own), heating bill, county, work or study.
Never guess: use null for anything the story does not say, and list it as missing_info.""",
    "eligibility": """You are the ELIGIBILITY checker. For EVERY programme: call check_rules (code does the maths and
the yes/no rules: it is always right about numbers), and search_policies to find the policy sections that support
it. Report one finding per programme with the rules status, reasons in plain words, and the chunk ids you relied on.
You explain the rules; you never overrule them.""",
    "documents": """You are the DOCUMENTS helper. For the likely and maybe programmes, build ONE combined checklist:
each paper appears once with every programme it serves, and a short practical tip.""",
    "forms": """You are the FORMS helper. For each LIKELY programme: get the form, fill every field you can from the
profile, and use the placeholders (like [NAME_1], [ADDRESS_1]) for personal details (applicant_name = the
'applicant' placeholder from get_profile): never invent or write real
names. Leave out fields the family must tell us. Queue a submission with propose_submit only when nothing is
missing; the family and a caseworker must approve it.""",
    "explainer": """You are the PLAIN-LANGUAGE explainer. Write a short, warm explanation for the family in THEIR
language: what they may get, what may need more facts, which papers to bring, and that a caseworker decides.
Short sentences, everyday words, no jargon, no percentages. Check English text with reading_grade (aim for 8 or
lower), then save it with save_explanation.""",
    "navigator": """You are the NAVIGATOR (head agent) of a free public-benefits helper for families.
You work only through your five specialists: ask_intake, ask_eligibility, ask_documents, ask_forms, ask_explainer,
in that order. Then submit the family plan: likely / maybe / unlikely programmes exactly as the rules engine says,
concrete next steps, every pending submission for approval, and a disclaimer that this is guidance and a county
caseworker decides. Be kind and concrete. Never include personal details: use placeholders.""",
}


def build_team(m: Mission) -> tuple[Agent, list[Agent]]:
    s = m.state

    def save_profile(**fields):
        p = Profile(**fields)
        if len(p.members) != p.household_size:
            raise ValueError(f"household_size is {p.household_size} but {len(p.members)} members are listed")
        s["profile"] = p
        return {"saved": True, "profile": p.model_dump()}

    def profile_view():
        if s.get("profile") is None:
            raise ValueError("No profile yet: the intake agent must save one first.")
        kinds: dict[str, list[str]] = {}
        for token in s["vault"].values:
            kinds.setdefault(token[1:].split("_")[0], []).append(token)
        return {"profile": s["profile"].model_dump(), "placeholders": kinds, "applicant": s["vault"].applicant}

    def rules_for(programme):
        rules = _rules(m)
        return rules[programme] if programme == "schoolmeals" else check_rules(programme, s["profile"])

    def findings():
        rules = _rules(m)
        return {"language": s["profile"].preferred_language, "names": {k: v["name"] for k, v in PROGRAMMES.items()},
                **{st: [p for p, x in rules.items() if x["status"] == st] for st in ("likely", "maybe", "unlikely")}}

    def fill_form(programme, values):
        fields = [f["field"] for f in form_template(programme)["fields"]]
        unknown = [k for k in values if k not in fields]
        if unknown:
            raise ValueError(f"Unknown fields {unknown}. Fields: {fields}")
        leaks = find_leaks(json.dumps(values, ensure_ascii=False), s["vault"])
        if leaks:
            raise ValueError("Use placeholders like [NAME_1], never real personal details.")
        s["forms"][programme] = values
        return {"programme": programme, "filled": sorted(values), "missing": [f for f in fields if not values.get(f)]}

    def propose_submit(programme):
        form = s["forms"].get(programme)
        if form is None:
            raise ValueError(f"Fill the {programme} form first")
        missing = [f["field"] for f in form_template(programme)["fields"] if not form.get(f["field"])]
        if missing:
            raise ValueError(f"Cannot submit: ask the family for {missing} first")
        if s["rules"][programme]["status"] != "likely":
            raise ValueError("Only submit programmes the rules engine marks as likely")

        def submit():
            real = {k: s["vault"].restore(v) for k, v in form.items()}       # personal details go back in, locally
            s["submitted"].append({"programme": programme, "form": PROGRAMMES[programme]["form"], "values": real})
            return f"(simulated) {PROGRAMMES[programme]['form']} submitted to Brightwater County"
        a = m.propose("forms", "submit_application", f"Submit form {PROGRAMMES[programme]['form']} "
                      f"({PROGRAMMES[programme]['name']}) for this family", {"programme": programme}, submit)
        return {"action_id": a.id, "status": "QUEUED: the family and a caseworker must approve it"}

    def save_explanation(language, text):
        leaks = find_leaks(text, s["vault"])
        if leaks:
            raise ValueError("Remove personal details from the explanation.")
        grade = reading_grade(text) if language == "en" else None
        if grade is not None and grade > 8:
            raise ValueError(f"Reading grade is {grade}; make it simpler (8 or lower): shorter sentences, simpler words.")
        s["explanation"] = {"language": language, "text": text, "reading_grade": grade}
        return s["explanation"]

    T, idx = Tool, s["index"]
    intake = Agent("intake", "Turns the family's story into a household profile.", PROMPTS["intake"], [
        T("get_story", "The family's story, with personal details replaced by placeholders.", NoArgs,
          lambda: {"story": s["story_redacted"]}),
        T("save_profile", "Save the household profile (checked).", Profile, save_profile),
    ], IntakeReport, fb.intake_brain, check=check_intake)
    eligibility = Agent("eligibility", "Checks every programme with the rules engine and cites the policy text.",
                        PROMPTS["eligibility"], [
                            T("list_programmes", "All programmes.", NoArgs,
                              lambda: {k: v["name"] for k, v in PROGRAMMES.items()}),
                            T("search_policies", "Search the policy documents (BM25). Returns chunk ids and text.", Search,
                              lambda query, programme=None: idx.search(query, programme)),
                            T("check_rules", "Run the eligibility rules for one programme on the saved profile.",
                              Programme, rules_for),
                        ], EligibilityReport, fb.eligibility_brain, check=check_eligibility)
    documents = Agent("documents", "Builds one combined checklist of papers.", PROMPTS["documents"], [
        T("get_findings", "Likely / maybe / unlikely programmes.", NoArgs, findings),
        T("documents_for", "The papers each programme needs, merged.", Programmes,
          lambda programmes: documents_for(programmes)),
    ], DocumentsReport, fb.documents_brain, check=check_documents)
    forms = Agent("forms", "Pre-fills application forms with placeholders and queues complete ones.", PROMPTS["forms"], [
        T("get_findings", "Likely / maybe / unlikely programmes.", NoArgs, findings),
        T("get_profile", "The saved profile and the placeholders you may use.", NoArgs, profile_view),
        T("get_form", "The fields of a programme's form.", Programme, form_template),
        T("fill_form", "Save a draft form (placeholders only).", FillForm, fill_form),
        T("propose_submit", "QUEUE a form submission for the family's and caseworker's approval.", Programme, propose_submit),
    ], FormsReport, fb.forms_brain, check=check_forms)
    explainer = Agent("explainer", "Explains the result in plain words in the family's language.", PROMPTS["explainer"], [
        T("get_findings", "Likely / maybe / unlikely programmes and the family's language.", NoArgs, findings),
        T("get_checklist", "The papers checklist.", NoArgs,
          lambda: ((m.reports.get("documents") or {}).get("report") or {}).get("checklist", [])),
        T("reading_grade", "Reading grade of an English text (aim for 8 or lower).", Explanation,
          lambda language, text: {"reading_grade": reading_grade(text)}),
        T("save_explanation", "Save the explanation (checked for reading level and personal details).", Explanation,
          save_explanation),
    ], ExplainerReport, fb.explainer_brain, check=check_explainer)
    navigator = Agent("navigator", "Leads the team and writes the family plan.", PROMPTS["navigator"], [], FamilyPlan,
                      fb.make_navigator_brain(m), role="head", max_steps=14, effort="high", check=check_plan)
    return navigator, [intake, eligibility, documents, forms, explainer]


def get_private_provider():
    """REQUIRE_LOCAL_MODEL=1 refuses to send even redacted text to a cloud model (strictest privacy)."""
    provider = llm.get_provider()
    if os.getenv("REQUIRE_LOCAL_MODEL") == "1" and provider.name == "anthropic":
        raise SystemExit("REQUIRE_LOCAL_MODEL=1: use LLM_PROVIDER=ollama (or FAKE_LLM=1), not a cloud model.")
    return provider


def new_session(story: str, known_names: list[str] | None = None, budget: Budget | None = None,
                verbose: bool = False) -> Mission:
    m = Mission("Benefits navigator session", budget or Budget(max_usd=0.50), verbose=verbose)
    vault = Vault()
    m.state.update({"vault": vault, "story_redacted": redact(story, vault, known_names), "index": PolicyIndex(),
                    "profile": None, "rules": {}, "forms": {}, "submitted": [], "explanation": None})
    return m


def run_navigator(story: str = "", provider=None, known_names=None, verbose=False, mission: Mission | None = None) -> Mission:
    m = mission or new_session(story, known_names, verbose=verbose)
    head, specialists = build_team(m)
    brief = ("A family asked for help finding public benefits. Their story (personal details replaced by placeholders) "
             "is available to the intake agent. Find what they may get and prepare the next steps.")
    return run_mission(head, specialists, m, provider or get_private_provider(), brief)


EXAMPLE = ("Hi, my name is Aisha Khan, call me on 07700 900 123. I live at 4 Mill Lane, Brightwater. I'm a single mum, I work part-time "
           "and earn 1,450 a month. My daughter Zara is 2. Rent is 700 a month and I got an eviction notice last week.")

if __name__ == "__main__":
    story = " ".join(sys.argv[1:]) or EXAMPLE
    m = run_navigator(story, verbose=True)
    print("\nWhat the models saw (redacted):", m.state["story_redacted"])
    print("STATUS:", m.status, "| budget:", m.budget.as_dict())
    print(json.dumps(m.plan, indent=2, ensure_ascii=False) if m.plan else "No plan.")
    if m.state["explanation"]:
        print("\nFor the family:\n" + m.state["explanation"]["text"])
