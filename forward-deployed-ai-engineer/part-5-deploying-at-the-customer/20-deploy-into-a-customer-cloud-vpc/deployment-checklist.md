# Deployment checklist: AI app in a customer cloud account

Copy this into the go-live ticket. Every line needs a name and a date. ⚙️ = `preflight.py` checks it for you.

## 1. Access and ownership (2-4 weeks before)
- [ ] Which account/project/subscription, which region, and who owns it at the customer (name, team)
- [ ] Your access: SSO user or a role you assume; no shared passwords; MFA on
- [ ] Change process: who approves deployments (change ticket, CAB meeting, maintenance window)
- [ ] Security review booked (it often takes 3-4 weeks: start first)

## 2. Network
- [ ] VPC/VNet address range agreed with the network team (no overlap with their other networks)
- [ ] App runs in **private** subnets; no public IP; no inbound from the internet
- [ ] How users reach it: VPN / Direct Connect / internal load balancer; DNS name agreed
- [ ] Outbound: none, or only through the customer's proxy with an allowlist
- [ ] ⚙️ Model endpoint resolves to **private** IPs (VPC endpoint / Private Service Connect / Private Endpoint)
- [ ] ⚙️ The open internet is not reachable from the app (if that is the policy)
- [ ] Endpoints also for: secrets manager, logs, container registry, object storage, remote shell (SSM / IAP / Bastion)

## 3. Identity and permissions
- [ ] The app uses a **role / service account / managed identity**, never long-lived keys on disk
- [ ] Least privilege: may call only the approved model(s), read only its own secret(s), write only its own logs
- [ ] Humans get shell access through the cloud's session manager, not SSH keys
- [ ] Break-glass procedure written down (who can get admin in an emergency, and how it is logged)

## 4. Secrets
- [ ] ⚙️ Every secret is present and loaded from a file or the secret manager (not baked into the image, not in Git)
- [ ] Secret values set by a customer admin; rotation date agreed; how to rotate is in the runbook
- [ ] Nothing secret in logs, traces, error pages or Terraform state

## 5. Data and model
- [ ] Data residency: model and data stay in the agreed region(s); written down in the DPA / security review
- [ ] Model provider and exact model id approved (e.g. Claude in Bedrock `anthropic.claude-opus-5-5`, or Vertex `claude-opus-5-5`)
- [ ] Model is enabled in this account/region (Bedrock model access / Vertex Model Garden) and quotas are enough for peak load
- [ ] Prompt and response logging decision: off / redacted / full, and retention period
- [ ] Fallback when the model is down (queue, local model, or "manual mode" for users)

## 6. Build and deploy
- [ ] Image built in CI, scanned, pushed to the **customer's** registry with a version tag (never `latest`)
- [ ] Infrastructure as code (Terraform) reviewed by the customer; state stored in their bucket with locking
- [ ] ⚙️ `/healthz` (alive) and `/ready` (configured) both return 200 after deploy
- [ ] Rollback tested once: previous image tag redeployed in under 10 minutes

## 7. Observability
- [ ] Logs go to the customer's log system; JSON; request id; no personal data
- [ ] Metrics: requests, errors, latency p95, model tokens and cost per day
- [ ] Alerts with an owner: app down, error rate, cost spike, model throttling (429)

## 8. Go-live
- [ ] Smoke test with the customer watching (5 real questions, answers checked)
- [ ] Runbook and on-call contacts handed over (lesson 22)
- [ ] Users informed: what it does, what it doesn't, how to report problems
- [ ] Decision recorded: go / no-go, by whom
