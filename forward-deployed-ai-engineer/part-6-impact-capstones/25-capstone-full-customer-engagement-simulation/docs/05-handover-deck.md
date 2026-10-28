---
marp: true
title: Northwind AI claims desk - handover
paginate: true
---

# Northwind AI claims desk
## Pilot results and handover
Kraków · 2027-02-22 · FDE team → Northwind IT and Claims

<!-- Speaker notes: 20 minutes + 10 for questions. Audience: Joanna, Dana, Marek, Tomasz, 8 handlers. -->

---

# Why we built it
- 600 claims a month, 8 handlers, **19 working days** to a decision
- 15 minutes per claim, but only **2 minutes** of real deciding
- 10 % of claims reopened because rules were applied by hand

---

# What it does
1. Reads the claims queue (EN / NL / PL)
2. Fetches TMS facts and the policy sections that apply
3. **Code** computes the outcome and the amount
4. Drafts the reply in the customer's language
5. **A person approves** every credit and every reply (supervisor above EUR 1,000)

---

# How it is built
- Head agent (claims lead) + 5 specialists, each with its own tools
- Rules as code, policy text as cited evidence (RAG)
- Propose → approve → execute; full trace per run
- Runs on Claude or on a local open model; FAKE mode for tests

---

# Results (pilot, weeks 1-6)  *(example numbers for the simulation)*
| Metric | Before | Pilot |
|---|---|---|
| Median time to decision | 19 days | 2.5 days |
| Handling time per claim | 15 min | 3.5 min |
| Reopened claims | 10 % | 2 % |
| Payments without correct approval | n/a | 0 |

---

# Safety
- Prompt injection in emails: flagged by code, amounts capped by policy, contract accounts only
- Supervisor rule enforced by the app, not by the model
- Golden-set evals in CI on every change, also with a 30 % flaky TMS

---

# What you own from today
- **Tomasz's team**: runbook (`docs/04-runbook.md`), deploys, secrets, on-call in working hours
- **Joanna**: policy changes and the golden set
- **FDE team**: second-line support until 2027-03-31

---

# Next steps (proposals)
1. Store runs in Postgres so approvals survive restarts
2. Phone claims (transcribed locally)
3. Weekly quality report: 20 random packs rated by handlers

---

# Questions?
Thank you, Joanna, Piotr, Eva, Tomasz and Marek.
