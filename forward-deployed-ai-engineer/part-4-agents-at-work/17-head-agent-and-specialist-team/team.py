"""team.py: a HEAD agent that plans, delegates to 4 SPECIALIST agents, checks their reports for conflicts,
asks follow-up questions, and writes one report for a human. Budgets and step limits keep it under control.

python make_data.py                    # once: creates northwind.db
python team.py --offline               # free: scripted stand-in models, real tools and data
python team.py                         # Claude: head + data analyst on CLAUDE_MODEL, others on CHEAP_MODEL
python team.py "Why did Express complaints rise in September?" --max-usd 0.50
"""
import argparse
import json
import threading
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field

import llm
from tools import TOOLSETS

SpecialistName = Literal["data_analyst", "operations", "customer_voice", "contracts"]
QUESTION = "Why did on-time delivery drop in September 2026 compared with August, and what should we do?"


# ======================= 1. Message formats (what agents send each other) =======================
class Task(BaseModel):                       # head -> specialist
    task_id: str
    specialist: SpecialistName
    question: str = Field(description="One clear question for this specialist")
    context: str = Field("", description="Anything the specialist should know, e.g. the period to compare")


class Finding(BaseModel):
    claim: str = Field(description="One sentence, with numbers")
    evidence: str = Field(description="Where it comes from: the query, table, note, ticket or document")
    confidence: Literal["low", "medium", "high"]


class Report(BaseModel):                     # specialist -> head
    status: Literal["complete", "partial"] = Field(description="partial if you ran out of steps or data")
    summary: str = Field(description="2-3 sentences")
    findings: list[Finding]
    recommendations: list[str]
    open_questions: list[str]


class PlannedTask(BaseModel):
    specialist: SpecialistName
    question: str
    why: str = Field(description="Why this specialist is needed for the goal")


class Plan(BaseModel):
    goal: str
    tasks: list[PlannedTask] = Field(description="At most one task per specialist")


class FollowUp(BaseModel):
    kind: Literal["conflict", "gap"] = Field(description="conflict = reports disagree; gap = a needed fact is missing")
    topic: str
    between: list[SpecialistName] = Field(description="The specialists involved")
    description: str
    ask: SpecialistName = Field(description="Who can settle it with data")
    question: str = Field(description="The follow-up question, including any numbers they need from other reports")


class Review(BaseModel):
    follow_ups: list[FollowUp] = Field(description="Empty if the reports agree and nothing important is missing")


class RootCause(BaseModel):
    cause: str
    evidence: str
    share_of_late_shipments: str = Field(description="e.g. 'about 50% (63 of 124 late shipments)'")
    confidence: Literal["low", "medium", "high"]


class Action(BaseModel):
    action: str
    owner: str
    expected_impact: str
    needs_human_approval: bool = Field(description="true for anything that spends money, changes contracts or contacts customers")


class FinalReport(BaseModel):                # head -> human
    answer: str = Field(description="3-4 sentence answer to the question")
    root_causes: list[RootCause]
    actions: list[Action]
    disagreements_resolved: list[str]
    open_questions: list[str]


# ======================= 2. Budgets and limits =======================
class BudgetExceeded(Exception):
    pass


@dataclass
class Budget:
    """One budget for the whole team. Every model call is charged here; when it's spent, agents must stop."""
    max_usd: float = 1.00
    max_calls: int = 60
    spent_usd: float = 0.0
    calls: int = 0
    by_agent: dict = field(default_factory=dict)
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False)

    def check(self, who: str):
        with self._lock:
            if self.calls >= self.max_calls or self.spent_usd >= self.max_usd:
                raise BudgetExceeded(f"{who}: team budget used up ({self.calls} calls, ${self.spent_usd:.3f})")

    def charge(self, who: str, reply: llm.Reply):
        with self._lock:
            self.calls += 1
            self.spent_usd += reply.cost_usd
            a = self.by_agent.setdefault(who, {"calls": 0, "usd": 0.0, "model": reply.model})
            a["calls"] += 1
            a["usd"] += reply.cost_usd


_print_lock = threading.Lock()


def log(who: str, text: str):
    with _print_lock:
        print(f"[{who:14s}] {text}")


def ask(who: str, budget: Budget, messages, **kwargs) -> llm.Reply:
    """Every model call in the team goes through here: budget check, call, charge."""
    budget.check(who)
    reply = llm.chat(messages, **kwargs)
    budget.charge(who, reply)
    return reply


# ======================= 3. Specialists =======================
SPECIALIST_PROMPTS = {
    "data_analyst": "You are the data analyst on Northwind Logistics' operations review team. You answer with numbers "
                    "from SQL queries on the shipments data. Compare periods, split by carrier, hub, week and cause.",
    "operations": "You are the operations specialist on Northwind Logistics' review team. You know carriers and hubs: "
                  "use the scorecard and the operations notes to explain WHAT happened on the ground and WHEN.",
    "customer_voice": "You are the customer-voice specialist on Northwind Logistics' review team. You read support "
                      "tickets: how many, about what, and what customers actually say. Quote short examples.",
    "contracts": "You are the contracts and policy specialist on Northwind Logistics' review team. You find what the "
                 "carrier contracts and customer policies say we are owed and what we owe. Use the calculator for money.",
}
SHARED_RULES = ("\nRules: use your tools; never invent numbers; say which tool result each finding comes from; "
                "stay within your speciality; stop calling tools once you can answer.")
REPORT_REQUEST = "Now write your report for the head of the review, based only on what your tools returned."


@dataclass
class Specialist:
    name: str
    model: str | None                    # None = the provider's default (lets Ollama users run everything locally)
    max_steps: int = 6                   # tool-calling rounds before it must report

    def run(self, task: Task, budget: Budget) -> Report:
        toolset = TOOLSETS[self.name]
        definitions = [d for d, _ in toolset]
        functions = {d["name"]: fn for d, fn in toolset}
        system = SPECIALIST_PROMPTS[self.name] + SHARED_RULES
        messages = [{"role": "user", "content": task.model_dump_json(indent=1)}]   # the Task message, as JSON
        status = "complete"
        try:
            for _ in range(self.max_steps):
                reply = ask(self.name, budget, messages, system=system, model=self.model, tools=definitions,
                            effort="low", max_tokens=4000)
                messages.append(reply.message)
                if not reply.tool_calls:
                    break
                for call in reply.tool_calls:
                    try:
                        result = functions[call["name"]](**call["args"])
                    except Exception as e:                       # bad arguments etc.: tell the model, carry on
                        result = f"ERROR: {type(e).__name__}: {e}"
                    log(self.name, f"🔧 {call['name']}({json.dumps(call['args'])[:70]}) -> {result[:70]}")
                    messages.append({"role": "tool", "id": call["id"], "content": result})
            else:
                status = "partial"                             # hit the step limit
            messages.append({"role": "user", "content": REPORT_REQUEST})
            report = ask(self.name, budget, messages, system=system, model=self.model, tools=definitions,
                         schema=Report, effort="low", max_tokens=4000).parsed
        except BudgetExceeded as e:
            log(self.name, f"⛔ {e}")
            return Report(status="partial", summary=f"Stopped early: {e}", findings=[], recommendations=[],
                          open_questions=["Budget ran out before this task finished."])
        if status == "partial":
            report.status = "partial"
        log(self.name, f"📋 report: {report.status}, {len(report.findings)} findings")
        return report


# ======================= 4. The head agent =======================
HEAD_SYSTEM = """You are the head of Northwind Logistics' operations review. You lead four specialists:
- data_analyst: SQL over shipments (dates, carrier, hub, region, service, dispatch and delivery dates, on_time)
- operations: carrier scorecards and operations notes (incidents at hubs and carriers)
- customer_voice: support tickets (counts, categories, what customers say)
- contracts: carrier contracts, customer compensation policy, project plans; can compute SLA service credits
You plan, delegate, compare reports, settle disagreements WITH DATA, and write a decision-ready report for a human
manager. Never invent numbers: use only what the reports contain. Anything that spends money, changes a contract
or contacts customers needs human approval."""


class Head:
    def __init__(self, budget: Budget, model: str | None = None, cheap_model: str | None = None):
        self.budget, self.model = budget, model
        self.team = {"data_analyst": Specialist("data_analyst", model),        # SQL needs the strong model
                     "operations": Specialist("operations", cheap_model),
                     "customer_voice": Specialist("customer_voice", cheap_model),
                     "contracts": Specialist("contracts", cheap_model)}
        self.reports: dict[str, Report] = {}

    def _ask(self, prompt: str, schema):
        return ask("head", self.budget, prompt, system=HEAD_SYSTEM, model=self.model, schema=schema,
                   effort="medium", max_tokens=8000).parsed

    def plan(self, question: str) -> list[Task]:
        plan = self._ask(f"<question>{question}</question>\nMake a plan: one focused task per specialist you need.", Plan)
        tasks = [Task(task_id=f"T{i}", specialist=t.specialist, question=t.question,
                      context="Compare September 2026 with August 2026.") for i, t in enumerate(plan.tasks[:4], start=1)]
        for t in tasks:
            log("head", f"🗂  {t.task_id} -> {t.specialist}: {t.question}")
        return tasks

    def delegate(self, tasks: list[Task]):
        """Specialists work at the same time (threads); each returns a Report."""
        with ThreadPoolExecutor(max_workers=4) as pool:
            futures = {t.task_id: pool.submit(self.team[t.specialist].run, t, self.budget) for t in tasks}
        for t in tasks:
            self.reports[t.task_id] = futures[t.task_id].result()

    def _reports_text(self, tasks: list[Task]) -> str:
        return "\n".join(f'<report task="{t.task_id}" specialist="{t.specialist}">\n'
                         f"{self.reports[t.task_id].model_dump_json(indent=1)}\n</report>" for t in tasks)

    def review(self, question: str, tasks: list[Task]) -> list[Task]:
        """Find contradictions and missing facts between reports; turn each into ONE follow-up task (max 3)."""
        review = self._ask(f"<question>{question}</question>\n{self._reports_text(tasks)}\n"
                           "Do any reports contradict each other or blame different causes for the same effect? "
                           "Is a fact missing that one specialist could get using another's numbers? "
                           "For each, choose who can settle it with data and what exactly to ask.", Review)
        follow_ups = []
        for i, f in enumerate(review.follow_ups[:3], start=1):
            log("head", f"⚖️  {f.kind} on '{f.topic}' ({', '.join(f.between)}) -> ask {f.ask}")
            follow_ups.append(Task(task_id=f"F{i}", specialist=f.ask, question=f.question,
                                   context=f"Follow-up ({f.kind}): {f.description}"))
        return follow_ups

    def synthesize(self, question: str, tasks: list[Task]) -> FinalReport:
        return self._ask(f"<question>{question}</question>\n{self._reports_text(tasks)}\n"
                         "Write the final report. Attribute shares of the late shipments to each root cause using "
                         "the follow-up numbers when there are any.", FinalReport)

    def run(self, question: str) -> FinalReport:
        log("head", f"🎯 {question}")
        tasks = self.plan(question)
        self.delegate(tasks)
        follow_ups = self.review(question, tasks)         # ONE review round: the head can't loop forever
        if follow_ups:
            self.delegate(follow_ups)
        return self.synthesize(question, tasks + follow_ups)


# ======================= 5. Output for the human =======================
def to_markdown(question: str, r: FinalReport, budget: Budget) -> str:
    lines = [f"# Operations review: {question}", "", r.answer, "", "## Root causes", "",
             "| Cause | Share of late shipments | Confidence | Evidence |", "|---|---|---|---|"]
    lines += [f"| {c.cause} | {c.share_of_late_shipments} | {c.confidence} | {c.evidence} |" for c in r.root_causes]
    lines += ["", "## Recommended actions", ""]
    lines += [f"{i}. {'**[NEEDS YOUR APPROVAL]** ' if a.needs_human_approval else ''}{a.action} "
              f"(owner: {a.owner}; expected impact: {a.expected_impact})" for i, a in enumerate(r.actions, start=1)]
    lines += ["", "## Disagreements we resolved", ""] + [f"- {d}" for d in r.disagreements_resolved]
    lines += ["", "## Open questions", ""] + [f"- {q}" for q in r.open_questions]
    lines += ["", f"_Cost: ${budget.spent_usd:.4f} in {budget.calls} model calls._"]
    return "\n".join(lines) + "\n"


def main():
    p = argparse.ArgumentParser()
    p.add_argument("question", nargs="?", default=QUESTION)
    p.add_argument("--offline", action="store_true", help="scripted stand-in models (free); tools and data are real")
    p.add_argument("--max-usd", type=float, default=1.00, help="team budget in dollars")
    p.add_argument("--max-calls", type=int, default=60, help="team budget in model calls")
    args = p.parse_args()
    if args.offline:
        import offline_brain
        from fake_llm import FakeClaude
        llm.set_client(FakeClaude(responder=offline_brain.respond))
        print("(offline: every agent's 'thinking' is scripted in offline_brain.py; tool calls, data and numbers are real)\n")
    claude = llm.PROVIDER == "claude"
    budget = Budget(args.max_usd, args.max_calls)
    head = Head(budget, model=llm.MODEL if claude else None, cheap_model=llm.CHEAP_MODEL if claude else None)
    final = head.run(args.question)
    report = to_markdown(args.question, final, budget)
    Path(__file__).with_name("report.md").write_text(report, encoding="utf-8")
    print("\n" + report)
    print("Cost by agent:")
    for who, a in budget.by_agent.items():
        print(f"  {who:14s} {a['model']:18s} {a['calls']:3d} calls  ${a['usd']:.4f}")
    print("Saved report.md")


if __name__ == "__main__":
    main()
