# Runbook: <service name>

> Lines starting with ">" are hints: replace them. A runbook is for a tired person at 3 am who has never seen this
> system: short sentences, exact commands, expected output, and when to escalate. Test every command before handover.

**Owner (team):** <who fixes it> · **Business owner:** <who decides about the service> · **Last tested:** <date, by whom>
**Where it runs:** <account / cluster / VM, region> · **Code:** <repo URL> · **Dashboards:** <links> · **Logs:** <where, query>

## 1. What it does
> 3-5 sentences: who uses it, for what, what it depends on (model provider, databases, APIs), and what happens when it is down.

## 2. Service levels
| SLI (what we measure) | SLO (target) | Where to see it |
|---|---|---|
| <e.g. requests without 5xx> | <e.g. 99.5 % per 30 days> | <dashboard> |

## 3. Contacts and escalation
| When | Who | How |
|---|---|---|
| First responder (on-call) | <rota name> | <pager / phone> |
| Escalation after <N> minutes | <name / team> | <how> |
| Model provider / vendor | <support plan, account id> | <portal / email> |
| Business decisions (switch off, tell users) | <name> | <how> |

## 4. Health checks
| Check | Command | Healthy looks like |
|---|---|---|
| <alive> | `<command>` | `<expected output>` |

## 5. Alerts and what to do
> One section per alert that can page someone. Same shape every time.

### <Alert name>
- **Means:** <in plain words>
- **Impact:** <who notices what>
- **Check first:** <commands / dashboards>
- **Fix:** <numbered steps>
- **Escalate if:** <condition, time limit>

## 6. Routine tasks
> Deploy, roll back, rotate secrets, renew certificates, update documents/policies, scale, back up and restore.

## 7. Known limits and decisions
> Things that look like bugs but are by design (and why).

## 8. Change log of this runbook
| Date | Change | By |
|---|---|---|
