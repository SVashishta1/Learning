# 8.8 · Capstone: an AI incident-response team

**What you'll build:** a realistic DevOps scenario. At 14:02 a deploy to `checkout-api` introduced a database-connection leak; by 14:15 customers can't check out. An **AI incident-response team** handles the page end to end, from first alert to a written postmortem, with you approving the fix.
**Like you're 10:** the school fire alarm goes off. One teacher checks how bad it is, one checks the cameras to see where it started, one grabs the emergency handbook, the head teacher decides what to do, but only the principal (you!) can approve evacuating the building. Afterwards someone writes "what happened and how we stop it happening again".
**Time:** ~4 h · **Builds on:** everything in Level 8, especially [8.7 Human-in-the-loop](../07-human-in-the-loop-file-organizer-agent) · **Needs:** an Anthropic API key (tests run without one)

```
 ALERT ─► Triage ─────────────► severity, impact, hypothesis (structured)
            ├─► Investigator ─► logs + metrics + deploy history → timeline & evidence   ┐ in parallel
            └─► Runbook expert ► finds the matching runbook steps                       ┘
         Commander ───────────► ONE decision with root cause & confidence (structured)
         Operator ────────────► executes it: rollback / restart / scale  ◄── 🧑 HUMAN APPROVAL
         Scribe ──────────────► blameless postmortem → incident_report.md
```

## Why this matters
When production breaks at 3 am, an on-call engineer has to read alerts, dig through logs, find what changed, look up the runbook, pick a fix, apply it carefully and write it up afterwards. AI agents that do the investigation and paperwork (with a human approving the action) are one of the most promising real uses of multi-agent systems, and "AI for SRE/DevOps" is a fast-growing area. This capstone combines every Level 8 pattern in one workflow you can demo in an interview.

## What you'll learn
- **Workflow of agents**: a fixed pipeline (triage → investigate → decide → act → document) where each step is a specialised agent.
- **Grounding in evidence**: agents read real logs, metrics and deploy history through tools instead of guessing.
- **Runbooks as retrieval**: company know-how steers the decision ("roll back, never scale a leak").
- **Separation of duties**: the agent that *decides* (Commander) isn't the one that *acts* (Operator), and a human approves the action.
- **Blameless postmortems**: the standard incident write-up, generated from the team's evidence and decisions.

## Before you start
```bash
cd level-8-multi-agent-systems/08-capstone-ai-incident-response-team
pip install -r requirements.txt
```
- `anthropic`: calls Claude. `pydantic`: tool inputs and the `TriageResult` / `Decision` schemas. `pytest`: tests.

**API key:** set `ANTHROPIC_API_KEY` as in the [Level 7 README](../../level-7-real-world-ai-apps/README.md#api-key-needed-from-here-on). Cheap mode: `export CLAUDE_MODEL=claude-haiku-5-5`. A full run with the default model costs roughly 10–30 cents.

## Run it
1. From the course root: `cd level-8-multi-agent-systems/08-capstone-ai-incident-response-team`
2. Tests (offline): `pytest -v`
3. Generate the incident data (logs, metrics, deploy history): `python make_incident.py`
4. Page the team: `python incident_team.py`
5. When the Operator asks, approve (`y`) or decline (`n`) the fix. A good team **rolls back v2.14.0 to v2.13.0**, not scales up: the runbook warns that scaling a leak makes it worse.
6. Read the postmortem in `incident_report.md`.

### What you should see
(Shortened and representative: wording, tool calls and costs vary.)
```
[Triage] 📋 TriageResult: severity='SEV1' affected_services=['checkout-api'] customer_impact='About 41% of checkout requests fail; ...
[Investigator] ▶ Incident: PagerDuty: checkout-api error rate 41% (threshold 2%), p95 latency 30s, since ~14:10 UTC ...
[RunbookExpert] ▶ Which runbook steps apply? ...
[Investigator] 🔧 recent_deploys({}) -> [ { "time": "2026-10-09T10:15", "service": "checkout-api", "version": "v2.13.0", ...
[Investigator] 🔧 search_logs({"pattern": "ERROR.*checkout|pool usage", "max_lines": 6}) -> 75 matching lines. First and last 3:
2026-10-13T14:03:43 WARN checkout-api db pool usage 15/50 (connections not returned: payment_retry handler)
[RunbookExpert] 🔧 search_runbooks({"query": "database connection pool exhausted after deploy"}) -> [database_connection_pool_exhausted.md] ...
[Commander] 📋 Decision: root_cause='v2.14.0 (deployed 14:02) added a payment_retry handler that does not return database connections, ...
[Operator] ▶ Execute: rollback_deploy on checkout-api to version v2.13.0. ...

⚠️  Operator wants to run rollback_deploy({"service": "checkout-api", "to_version": "v2.13.0", "reason": "connection leak introduced in v2.14.0"}). Allow? [y/N] y
[Operator] 🔧 rollback_deploy(...) -> (simulated) Rolled back checkout-api to v2.13.0. Error rate is recovering: 41% -> 0.4% in 6 minutes.
[Scribe] ✔ done (2841 chars)

# Postmortem: checkout-api outage, 2026-10-13

## Summary
A deploy of checkout-api v2.14.0 at 14:02 UTC introduced a database connection leak ...
## Action items
- Add a test that connections are returned (owner: checkout team)
- Alert at 80% pool usage (owner: SRE)

Saved incident_report.md

Token usage per agent:
  Triage  ...  Investigator  ...  RunbookExpert  ...  Commander  ...  Operator  ...  Scribe  ...
  TOTAL                  ≈ $0.1920
```
What to look at: the Investigator and RunbookExpert start at the same time; the Commander's root cause cites the 14:02 deploy and the "connections not returned" log lines; the rollback only ran after your `y`; the postmortem has a timeline and action items, and blames a process gap, not a person.

## How it works
1. **`make_incident.py`** writes `incident_data/` next to the script with a fixed random seed: `app.log` (one hour of logs; after 14:02 the pool fills by one connection every 30 s, then `QueuePool limit ... reached` errors and 503s), `metrics.json` (error rate, p95 latency and pool usage over time for three services) and `deploys.json` (checkout-api v2.13.0 on Oct 9, a search-api upgrade, and the bad checkout-api v2.14.0 at 14:02).
2. **Investigation tools** (`incident_team.py`): `search_logs(pattern, max_lines)` runs a case-insensitive regex over the log and returns the match count plus the first and last lines (when it started and how it is now, without flooding the context). `get_metrics(service)` and `recent_deploys()` return the JSON data. `search_runbooks(query)` ranks the Markdown runbooks by shared words and returns the top 2 (keyword retrieval, like a tiny 7.3).
3. **Action tools** `rollback_deploy`, `restart_service` and `scale_service` are *simulated* (they record to `ACTIONS_TAKEN` and return what would happen) and all have `needs_approval=True`. Note the realistic results: restarting only buys time, scaling pushes the database to 95% of its connections.
4. **Schemas.** `TriageResult` (severity SEV1–3, affected services, customer impact, first hypothesis) and `Decision` (root cause, confidence, one of four actions, service, `to_version` for rollbacks, reasoning). Using `Literal` means the Commander can only choose actions the Operator actually has.
5. **`build_team()`** creates six agents with focused prompts and only the tools each needs: Triage (no tools, `effort="low"`), Investigator (logs/metrics/deploys), RunbookExpert (runbook search), Commander (no tools, "never scale a connection leak"), Operator (the three action tools) and Scribe (blameless postmortem format).
6. **`respond(alert)`** runs the workflow: Triage reads the alert plus the metrics; a `ThreadPoolExecutor` runs the Investigator and the RunbookExpert in parallel; the Commander gets triage + evidence + runbook steps and returns one `Decision`; unless it's `monitor_only`, the Operator executes it (pausing for your approval); the Scribe writes the postmortem from everything, including the actions log.
7. **Tests** check the tools on the generated data (including that the last good version is in the deploy history), then run the whole team with a `RoleFake` that answers by agent role and an approver that records what it was asked, proving the rollback needed human approval.

## If something goes wrong
- **`Run: python make_incident.py`** → the incident data doesn't exist yet. Run that first (the tests also create it automatically).
- **The script seems stuck** → it's waiting for your `y`/`N` answer to the Operator's request.
- **The Commander chose `scale_service`** → read its `reasoning`. Usually the runbook step wasn't found: check the RunbookExpert's output, or make the Commander's prompt stricter ("follow the runbook order").
- **`anthropic.RateLimitError` (429)** → two agents call the API at once and new accounts have low limits. Wait a minute and re-run.
- **You declined the fix and the postmortem says nothing was done** → correct behaviour: the Operator reports the decline and the Scribe documents it. In real life a human would now act manually.

## Try this
1. **Don't over-react.** Page the team about the *search-api* instead: `alert = "Grafana: search-api p95 latency 1200 ms (threshold 1000 ms) for 5 minutes"`. The runbook says slow queries during the scheduled index rebuild are expected. Does the Commander choose `monitor_only`?
   <details><summary>Hint</summary>

   Change `alert` in `__main__` and run. The metrics show search-api at 0.4% errors and 420 ms p95 at 14:30, and `high_latency_search.md` says only to page above 2,000 ms for 15+ minutes. A good team decides `monitor_only` and the Operator never runs. Testing that agents *don't* act is as important as testing that they do.
   </details>
2. **A Comms agent.** Add an agent that drafts a customer status-page update and an internal Slack message from the triage and decision, and appends both to the report.
   <details><summary>Solution</summary>

   In `respond()`, after the decision:
   ```python
   comms = Agent("Comms", ("You write incident communications. Status page: calm, no internal details, no blame, "
                           "say what customers see and when to expect the next update. Slack: concise, technical, with next steps."),
                 client=client, verbose=verbose, effort="low")
   updates = comms.run(f"Triage: {tri.model_dump_json()}\nDecision: {decision.model_dump_json()}\n"
                       "Write a status-page update and a Slack message.")
   ```
   Add `updates` to the Scribe's prompt or append it to `report`, and add `comms` to the returned agents so it shows in the cost report.
   </details>
3. **Make it a service.** Wrap `respond()` in a FastAPI endpoint `POST /incidents` that receives alert webhooks (for example from the Grafana you set up in 7.6), runs the team in the background and stores the report.
   <details><summary>Hint</summary>

   Use FastAPI's `BackgroundTasks` so the webhook returns immediately. The CLI approver can't work on a server: pass an `approver` that saves a pending approval (in a dict or database) and waits until a human calls `POST /approvals/{id}` with yes/no, or posts a message with Approve/Decline buttons to Slack. Protect the endpoints with the API-key check from 7.6.
   </details>

## Check yourself
1. Why are the Investigator and RunbookExpert run in parallel, but the Commander only after both?
2. Why is the agent that decides (Commander) separate from the one that acts (Operator)?
3. Why would scaling up have made this incident worse?
4. What makes a postmortem "blameless", and why do teams insist on it?

<details><summary>Answers</summary>

1. They don't depend on each other, so running them together saves time. The Commander needs both the evidence and the runbook steps to decide, so it must wait.
2. Separation of duties: the decision is a structured, reviewable record, and the actor has only the tools for executing it, with a human approval gate in between. A single agent that both decides and acts can skip steps unnoticed.
3. It's a leak: every replica keeps leaking connections, so more replicas exhaust the database's `max_connections` faster (the simulated result warns about 95%), possibly taking down other services too.
4. It describes what happened and which process or safeguard failed, not who to blame. People then share information honestly, which is the only way to find and fix the real causes.
</details>

## Learn more (optional)
- Google SRE book, "Postmortem culture" (free): https://sre.google/sre-book/postmortem-culture/
- Building effective agents (Anthropic): https://www.anthropic.com/engineering/building-effective-agents
- How we built our multi-agent research system (Anthropic): https://www.anthropic.com/engineering/multi-agent-research-system

## Next
🎉 You've finished the **AI Engineer Journey**: from "Hello API" to a team of AI agents with human approval. What to do now:
1. **Build your portfolio.** Pin 4 projects on GitHub: the churn API (3.6), the RAG capstone (7.6), the support team (8.2) and this incident responder. Give each a README with a GIF or a 2-minute demo video and a short "trade-offs I made" section. See "Turn this into a job" in the [course README](../../README.md#turn-this-into-a-job).
2. **Add a new skill: voice.** Continue with → [Voice AI from Zero](../../../voice-ai-from-zero), 22 small projects from recording your voice to a fully private local voice assistant. Speech-to-text plus your Level 7–8 agents makes a talking assistant.
3. **Keep shipping.** Pick a real problem (your own notes, a club's documents, a family business's invoices) and build a small AI tool for it with what you've learned. Real users teach you more than any course.
