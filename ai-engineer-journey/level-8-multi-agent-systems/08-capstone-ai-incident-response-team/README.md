# 8.8 · Capstone: an AI incident-response team

**What you build:** a realistic DevOps scenario. At 14:02 a deploy to `checkout-api` introduced a database-connection leak; by 14:15 customers can't check out. An **AI incident-response team** handles the page end to end:

```
 ALERT ─► Triage ─────────────► severity, impact, hypothesis (structured)
            ├─► Investigator ─► logs + metrics + deploy history → timeline & evidence   ┐ in parallel
            └─► Runbook expert ► finds the matching runbook steps                       ┘
         Commander ───────────► ONE decision with root cause & confidence (structured)
         Operator ────────────► executes it: rollback / restart / scale  ◄── 🧑 HUMAN APPROVAL
         Scribe ──────────────► blameless postmortem → incident_report.md
```
It uses everything from Level 8: structured outputs, tools, parallel agents, RAG-style runbook search, human approval, and cost tracking.

**Like you're 10:** the school fire alarm goes off. One teacher checks how bad it is, one checks the cameras to see where it started, one grabs the emergency handbook, the head teacher decides what to do, but only the principal (you!) can approve evacuating the building. Afterwards someone writes "what happened and how we stop it happening again".

## Run it
```bash
cd level-8-multi-agent-systems/08-capstone-ai-incident-response-team
pip install -r requirements.txt
python make_incident.py               # generates logs, metrics and deploy history for the incident
export ANTHROPIC_API_KEY=sk-ant-...
python incident_team.py
```
When asked, approve (or decline) the remediation. A good team should **roll back v2.14.0**, not scale up (the runbook warns that scaling a leak makes it worse). The postmortem is saved to `incident_report.md`.

Tests (offline): `pytest -v`

## What makes this "production-grade" thinking
- **Grounded in evidence:** agents read real logs, metrics and deploy history through tools instead of guessing.
- **Runbooks as RAG:** company knowledge steers the decision (swap the keyword search for embeddings from 7.3).
- **Separation of duties:** the agent that *decides* (Commander) is not the one that *acts* (Operator), and a human approves the action.
- **Structured decisions** with confidence make the system auditable and testable.
- **Blameless postmortem:** the real-world SRE culture artifact, generated automatically.

## Your turn
1. Create a second incident with `make_incident.py` (e.g. the search-api index rebuild, which should be `monitor_only`) and check the team *doesn't* over-react.
2. Add a "Comms" agent that drafts a customer status-page update and an internal Slack message.
3. Turn the team into a service: FastAPI endpoint `/incidents` that receives alert webhooks (from Grafana in 7.6!) and posts approval requests to Slack.
4. **Put it on your CV:** record a 2-minute demo video of this running. Recruiters love seeing agents with human-in-the-loop safety.

## Read
- Google SRE book, "Postmortem culture" (free): https://sre.google/sre-book/postmortem-culture/
- Building effective agents: https://www.anthropic.com/engineering/building-effective-agents
