# 7.6 · Capstone: deploy a full AI app

**What you'll build:** a production-style **"Ask the handbook"** service. It takes the RAG engine from 7.3 and wraps it in everything a real company needs before letting users near it: API keys, rate limits, a daily spending cap, JSON logs, metrics, health checks, Docker, CI and a one-click cloud deploy.
**Like you're 10:** you built a lemonade stand that works in your kitchen. Now you're opening a real shop: a lock on the door (auth), a "max 20 cups per customer per minute" sign (rate limit), a cash register that stops when the day's lemon budget is used up (budget cap), a security camera (logs), and a dashboard showing sales (metrics).
**Time:** ~4 h · **Builds on:** [7.5 Evaluate your RAG](../05-evaluate-your-rag-and-chatbot) and [1.7 Dockerize & deploy](../../level-1-apis/07-dockerize-and-deploy-to-the-cloud) · **Needs:** an Anthropic API key (tests run without one); Docker Desktop for the full stack (optional)

| Production feature | Where |
|---|---|
| RAG answers with citations + document upload | `app/rag.py`, `POST /ask`, `POST /documents` |
| API-key auth (`X-API-Key` header) | `app/security.py` |
| Rate limiting (requests per minute per key) | `app/security.py` |
| **Daily spending cap** on LLM calls | `app/security.py` |
| Clean 502 error when Claude's API fails | `app/main.py` |
| Structured JSON logs with request ids | `app/observability.py` + middleware |
| Prometheus metrics: requests, latency, **tokens and $ cost** | `GET /metrics` |
| Health + readiness checks | `GET /health`, `GET /ready` |
| Docker image (non-root user, healthcheck) | `Dockerfile` |
| Local monitoring stack: Prometheus + Grafana | `docker-compose.yml` |
| CI tests with a fake LLM (free, no secrets) | `test_app.py`, `ci/github-actions-tests.yml` |
| One-click cloud deploy | `render.yaml` |

## Why this matters
A demo that works on your laptop is maybe 20% of the job. The rest is what this capstone adds: keeping strangers out, stopping one user (or bug) from running up a huge bill, knowing what's happening in production, and shipping safely with tests on every push. Interviewers love candidates who can talk about rate limits, cost caps and monitoring for LLM apps, because that's what breaks in real life. This is the project to pin on your GitHub.

## What you'll learn
- **API-key authentication**: only requests with a valid `X-API-Key` header get in.
- **Rate limiting and budget caps**: limits per minute per key, and a daily dollar limit on LLM spend.
- **Observability**: JSON logs (one searchable object per line) and Prometheus metrics (counters and histograms you can graph).
- **Health vs. readiness**: "the process is alive" vs. "it's ready to serve requests".
- **Containers, CI and deploys**: a Docker image, tests on every push with a fake LLM, and a blueprint file for Render.

## Before you start
```bash
cd level-7-real-world-ai-apps/06-capstone-deploy-a-full-ai-app
pip install -r requirements.txt
```
- `anthropic`: Claude. `numpy`, `scikit-learn`, `pypdf`: the RAG engine (TF-IDF embeddings by default here, to keep the Docker image small).
- `fastapi`, `uvicorn[standard]`, `python-multipart`: the API and uploads.
- `prometheus-client`: exposes metrics at `/metrics`.
- `httpx`, `pytest`: tests.
- Optional: `pip install sentence-transformers` and run with `EMBEDDER=auto` for meaning-based search (adds ~1 GB to an image).

**API key:** set `ANTHROPIC_API_KEY` as in the [Level 7 README](../README.md#api-key-needed-from-here-on). The app's own keys come from `APP_API_KEYS` (comma-separated); the default for local use is `dev-key-123`. Settings you can change with environment variables: `RATE_LIMIT_PER_MINUTE` (20), `DAILY_BUDGET_USD` (2.0), `EMBEDDER` (`auto` locally, `tfidf` in Docker), `DOCS_DIR` (`docs`), `CLAUDE_MODEL`.

## Run it
**A. Locally, no Docker**
1. From the course root: `cd level-7-real-world-ai-apps/06-capstone-deploy-a-full-ai-app`
2. Tests (offline, fake LLM): `pytest -v`
3. Start: `uvicorn app.main:app --reload`
4. Ask (in a second terminal):
   ```bash
   curl -X POST localhost:8000/ask -H "X-API-Key: dev-key-123" -H "Content-Type: application/json" \
        -d '{"question": "How much can I spend on hotels in London?"}'
   ```
   (Windows PowerShell: type `curl.exe` instead of `curl`. Or skip curl: open http://127.0.0.1:8000/docs → **POST /ask → Try it out**, fill the `x-api-key` box with `dev-key-123`, and press **Execute**.)
5. See the metrics: `curl localhost:8000/metrics | grep ai_`

**B. The full stack with Docker** (app + Prometheus + Grafana)
1. `export ANTHROPIC_API_KEY=sk-ant-...` then `docker compose up --build`
2. App: http://localhost:8000 (send `X-API-Key: dev-key-123` as above). Docker uses `claude-haiku-5-5` by default to keep it cheap.
3. Prometheus: http://localhost:9090 → try `rate(ai_requests_total[1m])` or `ai_cost_usd_total`.
4. Grafana: http://localhost:3000 → Connections → add a Prometheus data source at `http://prometheus:9090` → build a dashboard with requests, p95 latency (`histogram_quantile(0.95, rate(ai_request_seconds_bucket[5m]))`) and cost.

**C. Deploy to the cloud (Render)**: same steps as 1.7. New → Blueprint → point at this folder's `render.yaml`. Paste your `ANTHROPIC_API_KEY` in the Render dashboard (never in git). Render generates a random `APP_API_KEYS` value; find it under Environment.

**D. Turn on CI**: copy `ci/github-actions-tests.yml` to `.github/workflows/` at the **root** of your repo. Every push now runs the tests on GitHub's servers; a green check means safe to deploy.

### What you should see
Tests:
```
test_app.py::test_ask_requires_api_key_and_returns_citations PASSED
test_app.py::test_rate_limit_kicks_in PASSED
test_app.py::test_metrics_and_health PASSED
test_app.py::test_upload_rejects_bad_types PASSED
test_app.py::test_daily_budget_blocks_llm_calls PASSED
test_app.py::test_llm_failure_becomes_a_clean_502 PASSED
6 passed
```
The `curl` answer (shortened; Claude's wording varies):
```json
{"answer": "Hotels in London are reimbursed up to 180 euros per night [1].",
 "sources": [{"n": 1, "source": "expense_policy.md", "score": 0.125, "text": "# Acme Robotics: Travel and Expense Policy ..."}],
 "retrieved": ["expense_policy.md", "expense_policy.md", "vacation_policy.md", "vacation_policy.md"],
 "usage": {"input_tokens": 612, "output_tokens": 25}}
```
Without the header you get `{"detail": "Missing or invalid X-API-Key header"}` (401). The server's terminal shows one JSON log line per event:
```
{"ts": 1792038572.879, "level": "INFO", "msg": "ready", "chunks": 6, "embedder": "tfidf"}
{"ts": 1792038575.331, "level": "INFO", "msg": "answer", "key": "dev-…", "question_chars": 41, "cited": 1}
{"ts": 1792038575.333, "level": "INFO", "msg": "request", "id": "3c9572643cc9", "path": "/ask", "status": 200, "ms": 158}
{"ts": 1792038575.349, "level": "INFO", "msg": "request", "id": "6fd9ed39f83c", "path": "/ask", "status": 401, "ms": 1}
```
And `/metrics` (filtered):
```
ai_requests_total{endpoint="/ask",status="200"} 1.0
ai_requests_total{endpoint="/ask",status="401"} 1.0
ai_request_seconds_count{endpoint="/ask"} 2.0
ai_tokens_total{direction="input"} 612.0
ai_tokens_total{direction="output"} 25.0
ai_cost_usd_total 0.002948
```
What to look at: the log never contains the full API key or the question text (only its length): logs get shared widely, so keep secrets and personal data out. The cost counter is how you'd set an alert like "we spent more than $5 in an hour".

## How it works
```
request ─► observe() middleware (request id, timer)
             └► /ask ─► require_api_key (401? 429?) ─► check_budget (503?) ─► rag.answer() ─► Claude
                         ◄── answer + citations ◄── record_usage(): tokens + $ ─► add_spend()
          ◄─ response + x-request-id header; metrics updated; JSON log line written
Prometheus scrapes /metrics every 10 s ─► Grafana draws the graphs
```

1. **`app/main.py` → `lifespan()`** runs once at startup: builds the RAG index from `DOCS_DIR` and creates the Claude client, then logs `ready`. `GET /ready` returns 503 until the index exists; `GET /health` just says the process is alive. Cloud platforms use these to decide when to send traffic and when to restart a container.
2. **`observe()` middleware** wraps *every* request: it reuses an incoming `x-request-id` header or makes a new id, times the request, increments `REQUESTS` (by endpoint and status code), records `LATENCY`, adds the id to the response, and writes a JSON log line. The request id lets you find every log line of one user's problem.
3. **`POST /ask`** depends on `require_api_key` (FastAPI runs it first), then calls `check_budget()`, then `answer()` from `app/rag.py` (the same engine as 7.3). `record_usage()` turns the token counts into dollars and `add_spend()` adds them to today's total.
4. **`app/security.py`**: `require_api_key` compares the `X-API-Key` header with `APP_API_KEYS` (401 if wrong). The rate limiter keeps a `deque` of timestamps per key and drops those older than 60 s (a *sliding window*); if 20 are left, it answers 429 with `Retry-After: 60`. `check_budget()` resets the total at midnight and answers 503 once `DAILY_BUDGET_USD` is spent.
5. **`llm_failed()`** catches any `anthropic.APIError` (rate limited, overloaded, network failure) and returns a clean 502 "bad gateway" with a short message, instead of a crash and a stack trace.
6. **`POST /documents`** accepts only `.pdf`, `.md` or `.txt`, keeps just the file name (so `../../etc/x` can't escape `docs/`), saves it and rebuilds the index.
7. **`app/observability.py`** defines the Prometheus metrics: `Counter`s only go up (requests, tokens, dollars); a `Histogram` sorts latencies into buckets (≤0.1 s, ≤0.5 s, ...) so you can compute percentiles like p95. `JsonFormatter` prints each log record as one JSON object, merging any `extra_fields`.
8. **`Dockerfile`** starts from `python:3.12-slim`, installs requirements, copies only `app/` and `docs/`, switches to a non-root `appuser`, adds a `HEALTHCHECK` that calls `/health`, and runs uvicorn with **one** worker (the limiter, budget and metrics live in that process's memory). `docker-compose.yml` adds Prometheus (configured by `monitoring/prometheus.yml` to scrape `app:8000`) and Grafana.
9. **`test_app.py`** sets test settings through environment variables *before* importing the app, swaps in `FakeClient`, and checks auth, citations, the request-id header, rate limiting (3/minute in tests), health/ready/metrics, upload validation, the budget cap and the 502 path. `ci/github-actions-tests.yml` runs exactly these tests on GitHub.

## If something goes wrong
- **`500 Internal Server Error` on `/ask`, and the server log says `Could not resolve authentication method`** → `ANTHROPIC_API_KEY` isn't set in the terminal (or `docker compose` environment) running the server. Set it and restart.
- **`401 Missing or invalid X-API-Key header`** → add `-H "X-API-Key: dev-key-123"` (or whatever you set in `APP_API_KEYS`). On Render, copy the generated value from the Environment tab.
- **`429 Rate limit`** → you sent more than `RATE_LIMIT_PER_MINUTE` requests in 60 seconds. Wait a minute or raise the limit.
- **`503 Daily AI budget reached`** → the cap worked. Raise `DAILY_BUDGET_USD` or wait until tomorrow (it also resets when the server restarts, see *Try this* 3).
- **`docker compose` fails with "Cannot connect to the Docker daemon"** → start Docker Desktop first. If port 8000, 9090 or 3000 is busy, stop the other program or change the left side of `ports:` in `docker-compose.yml` (e.g. `"8001:8000"`).

## Try this
1. **Log what users ask about.** Add a counter `ai_unanswered_total` that goes up whenever the answer contains "couldn't find". Then you'll know which documents are missing.
   <details><summary>Solution</summary>

   In `app/observability.py`: `UNANSWERED = Counter("ai_unanswered_total", "Questions the documents couldn't answer")`. In `ask()` in `app/main.py`, after `answer(...)`:
   ```python
   if "couldn't find" in result["answer"].lower():
       UNANSWERED.inc()
   ```
   (import `UNANSWERED` at the top). In Grafana, graph `increase(ai_unanswered_total[1d])`. Add a test that scripts the fake reply "I couldn't find that in the documents." and checks the metric text.
   </details>
2. **Add chat with memory.** Add `POST /chat` behind the same `require_api_key` and `check_budget`, reusing the database and `history()` idea from 7.1.
   <details><summary>Hint</summary>

   Copy `db.py` from 7.1 into `app/` (change `import`s to `from app import ...`). The endpoint looks like 7.1's `send()`, plus `key: str = Depends(require_api_key)`, `check_budget()` first, and `add_spend(record_usage(llm.MODEL, ...))` after the call. Store `key` on each conversation so a user can only read their own chats.
   </details>
3. **Share limits across workers and restarts.** The rate limiter and budget live in memory, so a restart resets them and two workers would each count separately. Move them to **Redis**.
   <details><summary>Hint</summary>

   Add `redis` to `docker-compose.yml` (`image: redis:7`) and `requirements.txt`. For the rate limit use a key per minute: `n = r.incr(f"rl:{key}:{int(time.time() // 60)}")`, `r.expire(..., 60)`, reject if `n > RATE_LIMIT`. For the budget use `r.incrbyfloat(f"spend:{today}", usd)` and read it in `check_budget()`. Then you can safely raise `--workers`. (Prometheus metrics across workers need `prometheus_client`'s multiprocess mode; read its docs before you scale.)
   </details>

## Check yourself
1. What's the difference between `/health` and `/ready`, and why have both?
2. Why does the app have its own `X-API-Key` instead of letting users send their Anthropic key?
3. Why is a daily spending cap important for an LLM app in particular?
4. A user reports "it was slow at 3 pm". What in this project helps you investigate?

<details><summary>Answers</summary>

1. `/health` = the process is running (if not, restart it). `/ready` = it finished starting up (index built) and can serve users. A platform restarts on failed health checks and holds traffic until ready.
2. Your Anthropic key is a secret that costs you money; it must stay on the server. App keys can be given per user or customer, limited, and revoked without touching the real secret.
3. Every request costs real money, and a bug, a loop or an attacker can send thousands of requests. The cap turns "surprise $500 bill" into "service paused until tomorrow".
4. The latency histogram (p95 around 3 pm in Grafana), the JSON logs with `ms` per request, and request ids to follow one slow request. Token counts show whether it was just a long prompt.
</details>

## Learn more (optional)
- Made With ML (MLOps, free): https://madewithml.com/
- Prometheus in 100 seconds: https://www.youtube.com/results?search_query=prometheus+monitoring+explained+in+100+seconds
- The Twelve-Factor App: https://12factor.net/
- Render Blueprints docs: https://render.com/docs/infrastructure-as-code

## Next
You've finished Level 7. → [8.1 · Writer + critic reflection loop](../../level-8-multi-agent-systems/01-writer-and-critic-reflection-loop)
