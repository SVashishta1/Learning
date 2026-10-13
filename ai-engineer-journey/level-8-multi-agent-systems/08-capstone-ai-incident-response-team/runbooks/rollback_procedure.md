# Runbook: rolling back a deploy

1. Identify the last good version (`deploys.json` / deploy history).
2. Roll back with the deploy tool: `rollback <service> <version>`. Requires approval from the on-call engineer.
3. Watch the error rate and latency for 10 minutes. If they don't recover, escalate.
4. Open a post-incident ticket. Never re-deploy the bad version without a fix and a test.
