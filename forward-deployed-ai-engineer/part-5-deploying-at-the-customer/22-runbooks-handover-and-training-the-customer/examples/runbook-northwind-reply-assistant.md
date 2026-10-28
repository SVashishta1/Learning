# Runbook: Northwind Shipment Reply Assistant

**Owner (team):** Northwind IT platform team (Tomasz) · **Business owner:** Priya Raman, support team lead · **Last tested:** 2027-01-18, by Tomasz and the FDE team
**Where it runs:** AWS account `northwind-ai-prod`, eu-central-1, VM `northwind-assistant-vm` (private subnet, see lesson 20) · **Code:** internal Git `ai/reply-assistant` · **Dashboards:** CloudWatch dashboard "reply-assistant" · **Logs:** CloudWatch log group `/northwind-assistant`

## 1. What it does
Support agents open a HelpDesk ticket and press "Draft reply". The assistant looks up the shipment in the TMS replica, checks the delivery-terms policy and drafts a reply with Claude (Amazon Bedrock, EU region). An agent always edits and sends the reply; the assistant never emails customers. If it is down, agents work as before (manual lookups): slower, but nothing is lost.

## 2. Service levels
| SLI | SLO | Where to see it |
|---|---|---|
| Draft requests that don't fail with a 5xx | 99.5 % per 30 days (office hours) | dashboard, "availability" widget; `python slo_report.py` monthly |
| Drafts returned in under 8 seconds | 95 % | dashboard, "latency p95" |
| Drafts sent with little or no edit | ≥ 70 % (business metric, weekly) | HelpDesk report "AI draft edit distance" |

## 3. Contacts and escalation
| When | Who | How |
|---|---|---|
| First responder (office hours 08:00-18:00 CET) | IT platform on-call | PagerDuty service "reply-assistant" |
| Not fixed in 30 minutes, or data/privacy concern | Tomasz (IT), then Marek Nowak (security) | phone list in the IT wiki |
| Bedrock errors or quota | AWS Support, Business plan | AWS console → Support |
| Switch it off / tell agents | Priya Raman | Teams channel "support-leads" |
| Until 2027-03-31: second line | FDE team | shared Slack channel "#northwind-fde" |

## 4. Health checks
| Check | Command | Healthy looks like |
|---|---|---|
| Container running | `aws ssm start-session --target <instance-id>` then `docker ps` | `northwind/assistant:1.x.y ... Up ... (healthy)` |
| App ready | `curl -s localhost:8000/ready` (on the VM) | `{"ready":true,"provider":"bedrock",...}` |
| Network and secrets | `docker exec <container> python preflight.py` with `PRIVATE_ONLY=1 EXPECT_NO_INTERNET=1` | `0 failed` |
| Errors in the last hour | CloudWatch Logs Insights: `filter level = "ERROR" \| stats count() by bin(5m)` | 0 to a few |

## 5. Alerts and what to do

### ReplyAssistantDown (health check failing for 3 minutes)
- **Means:** the load balancer can't reach the app.
- **Impact:** agents see "Assistant unavailable" and work manually.
- **Check first:** `docker ps -a` on the VM. Exited? `docker logs --tail 100 <container>`.
- **Fix:** 1) `docker restart <container>`. 2) If it exits again, look for the first error in the log. 3) If it started after a deploy, roll back (section 6).
- **Escalate if:** not fixed in 30 minutes, or the VM itself is unreachable (SSM fails) → Tomasz.

### HighErrorBudgetBurn (5xx burn rate above 14.4x for 1 hour)
- **Means:** at this rate the whole month's error budget is gone in about 2 days.
- **Impact:** many drafts fail; agents retry and get frustrated.
- **Check first:** logs for `ThrottlingException` or `ServiceUnavailable` from Bedrock (provider problem) vs Python tracebacks (our problem); the AWS Health dashboard for Bedrock in eu-central-1.
- **Fix:** provider problem → post in "support-leads" that drafts are degraded, open an AWS support case, nothing else to do. Quota (`ThrottlingException`) → check usage vs quota in Service Quotas; request an increase. Our bug → roll back.
- **Escalate if:** longer than 1 hour → Priya decides whether to switch the button off for the day.

### SlowDrafts (p95 above 8 s for 30 minutes)
- **Means:** drafts are slow, usually a longer prompt, a bigger model or provider latency.
- **Check first:** did a deploy or prompt change happen today (change log)? Model id in `/ready`.
- **Fix:** roll back the prompt/model change; if none, open a provider case.

## 6. Routine tasks
- **Deploy a new version:** CI builds `northwind/assistant:<version>` and pushes it to ECR. On the VM: change the tag in `/opt/assistant/compose.yaml`, then `docker compose pull && docker compose up -d`, then the health checks above. Record it in the change log.
- **Roll back:** put the previous tag back in `compose.yaml`, `docker compose up -d`. Target: under 10 minutes.
- **Rotate secrets:** none for Bedrock (IAM role). The HelpDesk API token: update it in Secrets Manager (`aws secretsmanager put-secret-value ...`), then restart the container. Every 90 days; calendar owner Tomasz.
- **Policy documents changed (delivery terms):** Priya sends the new file; IT replaces it in `knowledge/`, runs the eval set (`python run_evals.py`, must stay ≥ 90 %), deploys.
- **Monthly SLO report:** export last month's request log and run `python slo_report.py requests.jsonl`; share with Priya.

## 7. Known limits and decisions
- English tickets only in the pilot; Dutch and Polish are phase 2.
- Prompts and answers are not stored (privacy decision, 2026-11-20); logs keep only ids, lengths, timings and errors.
- One VM, no automatic failover: agreed with Dana, because agents can always work manually.

## 8. Change log of this runbook
| Date | Change | By |
|---|---|---|
| 2027-01-18 | First version, all commands tested on prod | Tomasz + FDE team |
