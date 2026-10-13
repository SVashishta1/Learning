# Runbook: database connection pool exhausted

**Symptoms:** "QueuePool limit ... reached" or "connection timed out" errors, rising latency, 503s. Pool usage near its maximum.

**Common causes:** a code path that doesn't return connections (missing `finally`/context manager), a traffic spike, slow queries holding connections.

**Immediate mitigation (in order):**
1. If the problem started right after a deploy, **roll back** that deploy. This is the fastest, safest fix.
2. If no recent deploy: restart the affected service's pods to release leaked connections (temporary relief only).
3. Only scale replicas if the database has spare connection capacity (check max_connections first). Scaling a leak makes it worse.

**Follow-up:** add a test that checks connections are returned; add an alert at 80% pool usage.
