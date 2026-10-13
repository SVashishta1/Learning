"""Project 8.8 CAPSTONE: an AI incident-response team.

  alert -> Triage (structured severity)
        -> Investigator (logs/metrics/deploys tools)  ┐ run IN PARALLEL
        -> Runbook expert (searches runbooks)         ┘
        -> Commander decides a remediation; risky actions need HUMAN approval
        -> Scribe writes the postmortem (incident_report.md)

python make_incident.py && python incident_team.py
"""
import json
import re
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field

from agent_core import Agent, Tool, cost_report

DATA, RUNBOOKS = Path("incident_data"), Path("runbooks")
ACTIONS_TAKEN: list[str] = []


# ---------------- Tools ----------------
class LogSearch(BaseModel):
    pattern: str = Field(description="Case-insensitive regex, e.g. 'ERROR.*checkout'")
    max_lines: int = Field(20, description="How many matching lines to return")


class MetricIn(BaseModel):
    service: str


class NoArgs(BaseModel):
    pass


class RunbookSearch(BaseModel):
    query: str


class ServiceAction(BaseModel):
    service: str
    reason: str


class RollbackIn(BaseModel):
    service: str
    to_version: str
    reason: str


def search_logs(pattern: str, max_lines: int = 20) -> str:
    rx = re.compile(pattern, re.IGNORECASE)
    hits = [line for line in (DATA / "app.log").read_text().splitlines() if rx.search(line)]
    return f"{len(hits)} matching lines. First and last {max_lines // 2}:\n" + "\n".join(hits[: max_lines // 2] + ["..."] + hits[-(max_lines // 2):]) if hits else "No matches."


def get_metrics(service: str) -> str:
    return json.dumps(json.loads((DATA / "metrics.json").read_text()).get(service, "unknown service"))


def recent_deploys() -> str:
    return (DATA / "deploys.json").read_text()


def search_runbooks(query: str) -> str:
    words = set(re.findall(r"\w+", query.lower()))
    scored = sorted(RUNBOOKS.glob("*.md"), key=lambda p: -len(words & set(re.findall(r"\w+", p.read_text().lower()))))
    return "\n\n---\n\n".join(f"[{p.name}]\n{p.read_text()}" for p in scored[:2])


def rollback_deploy(service: str, to_version: str, reason: str) -> str:
    ACTIONS_TAKEN.append(f"ROLLBACK {service} -> {to_version} ({reason})")
    return f"(simulated) Rolled back {service} to {to_version}. Error rate is recovering: 41% -> 0.4% in 6 minutes."


def restart_service(service: str, reason: str) -> str:
    ACTIONS_TAKEN.append(f"RESTART {service} ({reason})")
    return f"(simulated) Restarted {service}. Pool usage dropped to 15/50 but is climbing again (+1 every 30s)."


def scale_service(service: str, reason: str) -> str:
    ACTIONS_TAKEN.append(f"SCALE {service} ({reason})")
    return f"(simulated) Scaled {service} to 6 replicas. WARNING: database max_connections now at 95%."


# ---------------- Structured outputs ----------------
class TriageResult(BaseModel):
    severity: Literal["SEV1", "SEV2", "SEV3"] = Field(description="SEV1 = customers broadly impacted / revenue loss")
    affected_services: list[str]
    customer_impact: str
    first_hypothesis: str


class Decision(BaseModel):
    root_cause: str
    confidence: Literal["low", "medium", "high"]
    action: Literal["rollback_deploy", "restart_service", "scale_service", "monitor_only"]
    service: str
    to_version: str | None = Field(description="Only for rollback: the last good version")
    reasoning: str


# ---------------- The team ----------------
def build_team(client=None, verbose=True, approver=None):
    kw = {"client": client, "verbose": verbose}
    if approver:
        kw["approver"] = approver
    triage = Agent("Triage", "You are an SRE on call. Assess incident severity quickly from the alert and metrics.", effort="low", **kw)
    investigator = Agent("Investigator", ("You investigate production incidents. Use logs, metrics and deploy history to find WHEN it "
                                          "started, WHAT changed and the evidence. Report a timeline and evidence with exact log lines."),
                         tools=[Tool("search_logs", "Regex search over application logs", LogSearch, search_logs),
                                Tool("get_metrics", "Error rate, latency and pool usage per service", MetricIn, get_metrics),
                                Tool("recent_deploys", "Recent deploys with versions and change notes", NoArgs, recent_deploys)], **kw)
    runbook = Agent("RunbookExpert", "You find and summarise the runbook steps that apply to the incident. Quote the exact steps.",
                    tools=[Tool("search_runbooks", "Search the team's runbooks", RunbookSearch, search_runbooks)], effort="low", **kw)
    commander = Agent("Commander", ("You are the incident commander. Decide ONE remediation following the runbook. Prefer the safest "
                                    "action that fixes the root cause. Never scale a connection leak."), **kw)
    operator = Agent("Operator", "You execute exactly the approved remediation using your tools, then report the result.",
                     tools=[Tool("rollback_deploy", "Roll back a service to a previous version", RollbackIn, rollback_deploy, needs_approval=True),
                            Tool("restart_service", "Restart a service", ServiceAction, restart_service, needs_approval=True),
                            Tool("scale_service", "Add replicas to a service", ServiceAction, scale_service, needs_approval=True)],
                     effort="low", **kw)
    scribe = Agent("Scribe", ("You write blameless postmortems in Markdown: Summary, Impact, Timeline (UTC), Root cause, "
                              "Resolution, What went well, Action items (with owners as roles)."), **kw)
    return triage, investigator, runbook, commander, operator, scribe


def respond(alert: str, client=None, verbose=True, approver=None) -> tuple[str, list[Agent]]:
    triage, investigator, runbook, commander, operator, scribe = team = build_team(client, verbose, approver)
    tri = triage.ask_structured(f"ALERT: {alert}\n\nMetrics snapshot:\n{(DATA / 'metrics.json').read_text()}", TriageResult)

    with ThreadPoolExecutor(max_workers=2) as pool:                  # investigation and runbook lookup in parallel
        evidence_f = pool.submit(investigator.run, f"Incident: {alert}\nTriage: {tri.model_dump_json()}\nFind the root cause.")
        steps_f = pool.submit(runbook.run, f"Which runbook steps apply? Incident: {alert}. Hypothesis: {tri.first_hypothesis}")
        evidence, steps = evidence_f.result(), steps_f.result()

    decision = commander.ask_structured(f"Triage: {tri.model_dump_json()}\n\nEvidence:\n{evidence}\n\nRunbook:\n{steps}", Decision)
    if decision.action == "monitor_only":
        result = "No action taken: monitoring."
    else:
        result = operator.run(f"Execute: {decision.action} on {decision.service}"
                              + (f" to version {decision.to_version}" if decision.to_version else "") + f". Reason: {decision.root_cause}")

    report = scribe.run(f"Write the postmortem.\nAlert: {alert}\nTriage: {tri.model_dump_json()}\nEvidence:\n{evidence}\n\n"
                        f"Decision: {decision.model_dump_json()}\nRemediation result: {result}\nActions log: {ACTIONS_TAKEN}")
    return report, list(team)


if __name__ == "__main__":
    if not (DATA / "app.log").exists():
        raise SystemExit("Run: python make_incident.py")
    alert = "PagerDuty: checkout-api error rate 41% (threshold 2%), p95 latency 30s, since ~14:10 UTC"
    report, agents = respond(alert)
    Path("incident_report.md").write_text(report)
    print("\n" + report + "\n\nSaved incident_report.md\n")
    print(cost_report(agents))
