# Runbook: search-api high latency

Slow queries during a scheduled index rebuild are expected and resolve by themselves within 2 hours. Only page someone if p95 latency is > 2000 ms for 15+ minutes or the error rate is > 2%.
