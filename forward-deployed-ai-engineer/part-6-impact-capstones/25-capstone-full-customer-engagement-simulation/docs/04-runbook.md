# Runbook: Northwind AI claims desk

**Service owner:** Tomasz (Northwind IT) · **Business owner:** Joanna Wiśniewska · **Escalation:** FDE team (until 2027-03-31), then Northwind IT
**Where it runs:** Kubernetes namespace `northwind-claims` (deployments `claims-desk`, and in test `mock-api`) · **Repo:** this folder
**SLOs:** page available 99.5 % of working hours; a batch of 50 claims processed in under 10 minutes; 0 payments without the right approval.

## 1. What it does (one paragraph)
Handlers press "Process the claims queue". A head agent and five specialists read new HelpDesk claim tickets, fetch TMS facts, find policy sections, compute the outcome with code, and draft replies. Nothing is paid or sent until a handler (or a supervisor above EUR 1,000) approves it on the page; then the app calls the Finance and HelpDesk APIs.

## 2. Health checks
| Check | Command | Healthy looks like |
|---|---|---|
| Pods running | `kubectl -n northwind-claims get pods` | `claims-desk-...  1/1  Running` |
| App alive | `kubectl -n northwind-claims port-forward svc/claims-desk 8080:80` then `curl localhost:8080/healthz` | `{"ok":true}` |
| Which brain | `curl localhost:8080/api/info` | `{"provider":"anthropic"}` (or `ollama`) |
| Recent errors | `kubectl -n northwind-claims logs deploy/claims-desk --since=1h \| grep -i error` | nothing, or isolated 503 retries |

## 3. Common incidents
### 3.1 A run ends with status `error`
1. Open the run on the page; read the last lines of the **Trace**.
2. `HTTPStatusError ... 503` from the TMS for many minutes → the TMS gateway is down. Tell Tomasz's team; handlers work manually; re-run later. Nothing was paid.
3. `AuthenticationError` → the `ANTHROPIC_API_KEY` secret is wrong or expired. Rotate it (section 5).

### 3.2 Status `budget_exceeded`
A run hit the dollar/token/tool-call cap (default $2). Look at the trace for a loop (the same tool again and again). Re-run once; if it repeats, open a ticket for the FDE team with the run id. Do not raise the budget to "make it pass".

### 3.3 A handler reports a wrong amount
1. Do **not** approve it. Reject the credit on the page with a note.
2. Check the assessment reasons on the page against the policy. If the code is wrong, it's a bug: add the ticket to `evals/golden.json` with the correct expected amount, fix `claims_tools.assess`, and let CI prove it.
3. If the policy changed, follow section 4.

### 3.4 A suspicious email (marked ⚠)
Approve nothing for that claim until the fraud team has looked at it. Credits always go to the contract account, but replies could still confirm details to a fraudster.

## 4. Planned change: a new policy version
1. Joanna sends the new Markdown files. Replace `policies/*.md`.
2. Update the rules in `claims_tools.py` (limits, days) if they changed; update `evals/golden.json` expectations.
3. Open a pull request. CI runs tests and evals. Two approvals: one from IT, one from Joanna.
4. Deploy (section 5) and announce in the claims team channel.

## 5. Deploy, roll back, rotate secrets
- Deploy a new version: build and push the image with a new tag, change `image:` in `k8s/claims-desk.yaml`, `kubectl apply -k k8s/`, then `kubectl -n northwind-claims rollout status deploy/claims-desk`.
- Roll back: `kubectl -n northwind-claims rollout undo deploy/claims-desk`.
- Rotate the API key: `kubectl -n northwind-claims create secret generic claims-desk-secrets --from-literal=ANTHROPIC_API_KEY=... --from-literal=MOCK_CLIENT_SECRET=... --dry-run=client -o yaml | kubectl apply -f -`, then `kubectl -n northwind-claims rollout restart deploy/claims-desk`.
- Switch to the local model (for example if the cloud provider is down): set `FAKE_LLM: "0"`, `LLM_PROVIDER: "ollama"` in the ConfigMap, apply, restart. Expect slower runs.

## 6. Known limits
- Runs are kept in memory: a restart forgets unfinished approvals (the tickets stay in HelpDesk; just re-run). Keep one replica.
- FAKE mode (`FAKE_LLM=1`) is for tests and demos only; it uses keyword rules.
