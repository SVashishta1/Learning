# 7.6 · Capstone: deploy a full AI app

**What you build:** a production-style **"Ask the handbook"** service. It takes the RAG engine from 7.3 and wraps it in everything a real company needs before letting users near it:

| Production feature | Where |
|---|---|
| RAG answers with citations + document upload | `app/rag.py`, `POST /ask`, `POST /documents` |
| API-key auth (`X-API-Key` header) | `app/security.py` |
| Rate limiting (requests/minute per key) | `app/security.py` |
| **Daily spending cap** on LLM calls | `app/security.py` |
| Structured JSON logs with request ids | `app/observability.py` + middleware |
| Prometheus metrics: requests, latency, **tokens and $ cost** | `GET /metrics` |
| Health + readiness checks | `GET /health`, `GET /ready` |
| Docker image (non-root user, healthcheck) | `Dockerfile` |
| Local monitoring stack: Prometheus + Grafana | `docker-compose.yml` |
| CI tests with a fake LLM (free, no secrets) | `test_app.py`, `ci/github-actions-tests.yml` |
| One-click cloud deploy | `render.yaml` |

**Like you're 10:** you built a lemonade stand that works in your kitchen. Now you're opening a real shop: a lock on the door (auth), a "max 20 cups per customer per minute" sign (rate limit), a cash register that stops when the day's lemon budget is used up (budget cap), a security camera (logs), and a dashboard showing sales (metrics).

## Run locally (no Docker)
```bash
cd level-7-real-world-ai-apps/06-capstone-deploy-a-full-ai-app
pip install -r requirements.txt
export ANTHROPIC_API_KEY=sk-ant-...
uvicorn app.main:app --reload
curl -X POST localhost:8000/ask -H "X-API-Key: dev-key-123" -H "Content-Type: application/json" \
     -d '{"question": "How much can I spend on hotels in London?"}'
curl localhost:8000/metrics | grep ai_
```
Tests: `pytest -v`

## Run the full stack with Docker
```bash
export ANTHROPIC_API_KEY=sk-ant-...
docker compose up --build
```
- App: http://localhost:8000 (send the header `X-API-Key: dev-key-123` with curl, as above, or with Postman)
- Prometheus: http://localhost:9090 → try the query `rate(ai_requests_total[1m])` or `ai_cost_usd_total`
- Grafana: http://localhost:3000 → Connections → add the Prometheus data source at `http://prometheus:9090` → build a dashboard with requests, p95 latency (`histogram_quantile(0.95, rate(ai_request_seconds_bucket[5m]))`) and cost.

## Deploy to the cloud (Render)
Same steps as project 1.7: New → Blueprint → point at this folder's `render.yaml`. Paste your `ANTHROPIC_API_KEY` in the Render dashboard (never in git). Render generates a random `APP_API_KEYS` value; find it under Environment.

## Turn on CI
Copy `ci/github-actions-tests.yml` to `.github/workflows/` at the root of your repo. Every push now runs the tests on GitHub's servers. Green checkmark = safe to deploy.

## Your turn
1. Add `/chat` with memory (reuse 7.1) behind the same auth and budget.
2. Store every question, answer, latency and cost in Postgres, and build a Grafana panel of "questions we couldn't answer". That's your list of missing documents.
3. Add the eval from 7.5 to CI so a prompt change that lowers accuracy fails the build.
4. The rate limiter and budget live in memory, so with `--workers 2` each worker counts separately and a restart resets them. Move both to **Redis** so they're shared and persistent.

## Read / watch
- Made With ML (MLOps, free): https://madewithml.com/
- Prometheus in 100 seconds: https://www.youtube.com/results?search_query=prometheus+monitoring+explained+in+100+seconds
- 12-factor app: https://12factor.net/
