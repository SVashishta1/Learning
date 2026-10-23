# 13 · Queues and background workers

**What you'll build:** a "take a ticket, come back later" way to ask the AI. The gateway puts each question in a **Redis queue** and answers at once with a job ID; separate **worker** containers pick up jobs, do the slow LLM work, and save the answer; your client **polls** until it's done. Then you add more workers with one command and watch the queue drain faster.
**Like you're 5:** at a busy bakery you don't stand at the oven. You get a numbered ticket, the bakers take tickets from the pile one by one, and the screen shows "number 42 is ready".
**Time:** ~60 min · **Builds on:** [12 · Split an AI app into services](../12-split-an-ai-app-into-services) · **Needs:** Docker with Compose; no API key

## Why this matters
LLM calls are slow (seconds to minutes for long documents or agents), and web requests that hang that long time out, block servers and frustrate users. Real AI products (document summarisers, report generators, batch classifiers, agent runs) almost always accept the work, return a job ID, and let **background workers** do it. Queues also smooth out traffic spikes and let you scale the expensive part separately.

## What you'll learn
- **Queue**: a waiting line of jobs. Producers add jobs at one end, workers take them from the other.
- **Worker**: a program with no web address that loops forever: take a job → do it → save the result.
- **Asynchronous API**: `POST /jobs` answers **202 Accepted** with a job ID right away; `GET /jobs/{id}` tells you the status.
- **Polling**: the client asks "is it done yet?" every second or so.
- **Horizontal scaling**: more workers = more jobs at the same time, with no code change.

## Before you start
- Docker with Compose (same as lesson 12). This lesson re-uses lesson 12's `rag-service` and `llm-service` folders, so keep them.
- For the polling script, your venv with the part's packages:
  ```bash
  pip install fastapi "uvicorn[standard]" httpx anthropic redis pytest
  ```
  (`httpx` is what `ask_async.py` uses.)
- No API key needed (`FAKE_LLM=1`). To make jobs visibly "slow", the compose file tells the fake LLM to take 3 seconds per answer (`DELAY_SECONDS`).
- Stop lesson 12 first if it's still running (`docker compose down` in its folder), because both use port 8000.

## Run it
1. Go into the lesson folder:
   ```bash
   cd part-3-microservices/13-queues-and-background-workers
   ```
2. Build and start everything (redis, rag-service, llm-service, gateway, worker):
   ```bash
   docker compose up -d --build
   ```
3. Submit one job:
   ```bash
   curl -X POST http://localhost:8000/jobs -H "Content-Type: application/json" -d '{"question": "Do you have oat milk?"}'
   ```
   Copy the `job_id` from the answer.
4. Ask for its status. Replace `JOB_ID` with yours; repeat a few times over ~4 seconds:
   ```bash
   curl http://localhost:8000/jobs/JOB_ID
   ```
5. Send 5 jobs at once and let the script poll for you:
   ```bash
   python ask_async.py
   ```
6. Now hire two more workers and run the script again:
   ```bash
   docker compose up -d --scale worker=3
   python ask_async.py
   ```
7. Watch the workers' own log lines:
   ```bash
   docker compose logs worker
   ```
8. Stop one worker politely and read how it says goodbye:
   ```bash
   docker compose stop worker
   docker compose logs worker --tail 3
   ```
9. Clean up: `docker compose down`.

**Command, piece by piece**

| Piece | Meaning |
|---|---|
| `docker compose up -d --scale worker=3` | make sure there are exactly 3 containers of the `worker` service (adds 2; the others are left alone) |
| `docker compose stop worker` | send every worker the signal **SIGTERM** ("please finish and exit"), wait up to 10 s, then force-kill |
| `docker compose logs worker --tail 3` | only the last 3 log lines of each worker |
| `python ask_async.py` | run the polling client; give questions as extra words in quotes, e.g. `python ask_async.py "Can I bring my dog?"` |

### What you should see
Step 3 (returns in a few milliseconds, even though the answer takes 3 seconds):
```
{"job_id":"99cef07e0ceb","status":"queued","status_url":"/jobs/99cef07e0ceb"}
```
Step 4, first while the worker is busy, then when it's done:
```
{"id":"99cef07e0ceb","status":"running","question":"Do you have oat milk?","created_at":"1792677520.9416015","worker":"99447aa45846","started_at":"1792677520.9451606"}
{"model":"fake-llm","started_at":"1792677520.9451606","created_at":"1792677520.9416015","question":"Do you have oat milk?","id":"99cef07e0ceb","worker":"99447aa45846","answer":"(fake LLM) Based on 1 document(s): We offer whole milk, skimmed milk, oat milk, almond milk and soy milk.","status":"done","sources":["Milk options"],"finished_at":"1792677523.970487"}
```
Step 5 with **one** worker (shortened): jobs finish one by one, ~3 s apart, all by the same worker:
```
all 5 submitted in 0.28s
[  1.9s] still waiting for 5 job(s)...
[  4.4s] 6dc7435af832 done   by 99447aa45846: (fake LLM) Based on 2 document(s): Free Wi-Fi is available in every shop.
[  7.5s] 9d4767a064e6 done   by 99447aa45846: (fake LLM) Based on 1 document(s): We offer whole milk, skimmed milk, oat milk, almond milk and soy milk.
...
[ 16.3s] 322764a56af4 done   by 99447aa45846: (fake LLM) Based on 1 document(s): If your drink is wrong, tell the barista and we will make a new one for free.

finished in 16.3s
```
Step 6 with **three** workers: three different worker names, about 3 times faster:
```
all 5 submitted in 0.32s

[  1.8s] still waiting for 5 job(s)...
[  3.1s] still waiting for 5 job(s)...
[  4.4s] 743cf3df2ea2 done   by 045ab1eefb47: (fake LLM) Based on 2 document(s): Free Wi-Fi is available in every shop.
[  4.5s] c7164056d766 done   by ddb1539195b5: (fake LLM) Based on 1 document(s): We offer whole milk, skimmed milk, oat milk, almond milk and soy milk.
[  4.5s] still waiting for 3 job(s)...
[  5.9s] still waiting for 3 job(s)...
[  7.0s] 45637046e221 done   by 99447aa45846: (fake LLM) Based on 1 document(s): Moonbeam Coffee is open from 7am to 7pm on weekdays and from 8am to 5pm on weekends.
[  7.2s] 560c0f5fcf60 done   by 045ab1eefb47: (fake LLM) Based on 1 document(s): Dogs are welcome on the terrace and inside our Riverside shop.
[  7.3s] d53b4022e069 done   by ddb1539195b5: (fake LLM) Based on 1 document(s): If your drink is wrong, tell the barista and we will make a new one for free.

finished in 7.3s
```
Step 8:
```
[0a4c4e54bb10] got signal 15, finishing current job then stopping
[0a4c4e54bb10] job 8f7bcbd946c7 done
[0a4c4e54bb10] stopped cleanly
```
Look at: `submitted in 0.3s` (the web part stays fast no matter how slow the AI is), the `by <worker>` names, and the total time going from ~16 s to ~7 s. Your times and IDs will differ.

## How it works

```mermaid
sequenceDiagram
    participant C as Client (ask_async.py)
    participant G as gateway
    participant Q as Redis
    participant W as worker (1..N)
    participant S as rag-service + llm-service
    C->>G: POST /jobs {"question"}
    G->>Q: HSET job:ID status=queued ; LPUSH queue:jobs ID
    G-->>C: 202 {"job_id": ID}
    W->>Q: BRPOP queue:jobs (wait for a job)
    Q-->>W: ID
    W->>Q: HSET job:ID status=running
    W->>S: search, then generate (slow)
    S-->>W: answer
    W->>Q: HSET job:ID status=done answer=...
    loop every second
        C->>G: GET /jobs/ID
        G->>Q: HGETALL job:ID
        G-->>C: {"status": "queued" / "running" / "done"}
    end
```

### Redis in 4 commands
**Redis** is a very fast in-memory database (you met it as a cache in [lesson 09](../../part-2-docker/09-docker-compose-multi-container-apps)). Here it plays two roles: the queue (a **list**) and the job notebook (one **hash** per job).

| Redis command | Python (`redis` package) | What it does here |
|---|---|---|
| `HSET job:ID status queued ...` | `store.hset(key, mapping={...})` | write fields into the job's "dictionary" |
| `EXPIRE job:ID 3600` | `store.expire(key, 3600)` | auto-delete the job record after 1 hour |
| `LPUSH queue:jobs ID` | `store.lpush(QUEUE, job_id)` | add the ticket at the **left** end of the list |
| `BRPOP queue:jobs 5` | `store.brpop([QUEUE], timeout=5)` | **B**locking **R**ight **POP**: wait up to 5 s for a ticket and take it from the **right** end |
| `HGETALL job:ID` | `store.hgetall(key)` | read the whole job record |
| `LLEN queue:jobs` | `store.llen(QUEUE)` | how many tickets are waiting |

Left in, right out = first in, first out (**FIFO**), like a real queue. Redis hands each ticket to exactly **one** waiting worker, so two workers never do the same job.

### gateway v1.1 (`gateway/main.py`)
1. Same `/ask` and `/health` as lesson 12, plus `REDIS_URL` and a Redis client: `redis.Redis.from_url(REDIS_URL, decode_responses=True)`. `decode_responses=True` gives you normal strings instead of bytes.
2. `POST /jobs` (`status_code=202` = "Accepted: I'll do it later"): makes a short random `job_id`, writes the job hash with status `queued`, sets a 1-hour expiry, pushes the ID onto `queue:jobs`, and returns immediately.
3. `GET /jobs/{job_id}` reads the hash. An empty result means the ID is wrong or expired → 404. The `sources` field was stored as JSON text, so it's turned back into a list.
4. `GET /queue` returns the queue length: a handy number to watch (and, later, to scale workers on).

### worker (`worker/worker.py`)
1. `main()` loops `while running:` and calls `store.brpop([QUEUE], timeout=5)`. It waits without using CPU until a job arrives. Every 5 s with no job it wakes up, which gives it a chance to notice a stop request.
2. `process(job_id)` marks the job `running` (with the worker's name, the container hostname), calls rag-service then llm-service exactly like the gateway's `/ask`, and stores `done` + `answer` + `sources`. Any HTTP problem stores `failed` + `error` instead, so the client is never left waiting forever.
3. `signal.signal(signal.SIGTERM, stop)`: when Docker (or Kubernetes) wants to stop the container it sends **SIGTERM**. The `stop()` handler only flips `running = False`, so the current job finishes before the loop ends. This is a **graceful shutdown**.
4. The worker's `httpx` timeout is 120 s, much longer than a web request could wait. That's the point of background work.

### `compose.yaml` (new parts)

| Key | Meaning |
|---|---|
| `worker:` with no `ports:` | nobody calls the worker; it calls out. No published port needed |
| `redis: image: redis:7-alpine` + `healthcheck` | the official Redis image; `redis-cli ping` answers `PONG` when it's ready |
| `build: ../12-split-an-ai-app-into-services/rag-service` | build from lesson 12's folder. `..` means "one folder up" |
| `DELAY_SECONDS: ${LLM_DELAY_SECONDS:-3}` | make the fake LLM slow (3 s) so you can watch statuses change. `LLM_DELAY_SECONDS=0 docker compose up -d` turns it off |

### Is the job safe if a worker crashes?
Not completely. `BRPOP` removes the ticket from the queue the moment a worker takes it. If that worker's container is killed mid-job (power cut, `docker kill`, out of memory), the job stays `running` forever. Graceful shutdown covers the *polite* stop. For crashes, real systems use a "reliable queue" (`BLMOVE` into a per-worker "processing" list, and a janitor that re-queues old entries) or a ready-made library or service: RQ, Celery, Arq, Dramatiq, or a cloud queue such as Amazon SQS or Google Pub/Sub. Exercise 3 below gets you started.

## If something goes wrong
- **`Bind for 0.0.0.0:8000 failed: port is already allocated`** → lesson 12 (or something else) still uses port 8000. Run `docker compose down` in lesson 12's folder.
- **Jobs stay `queued` forever** → no worker is running or it can't reach Redis. `docker compose ps worker` and `docker compose logs worker`. If you scaled to 0 or stopped it, run `docker compose up -d`.
- **A job says `failed` with `ConnectError`** → the worker couldn't reach rag-service or llm-service. Check `docker compose ps` and that `RAG_URL`/`LLM_URL` use the service names, not `localhost`.
- **`{"detail":"no such job (wrong ID, or it expired)"}`** → typo in the ID, or more than 1 hour passed (`JOB_TTL_SECONDS`), or you ran `docker compose down` (Redis here keeps data only in memory, so jobs vanish with the container).
- **`ask_async.py` says `httpx.ConnectError`** → the gateway isn't up yet (wait for `docker compose ps` to show it healthy) or your venv lacks `httpx`.

## Try this
1. Run `python ask_async.py` with 10 questions of your own and `--scale worker=5`. How long does it take compared to 1 worker? What stops it from getting faster forever?
2. Watch Redis directly: `docker compose exec redis redis-cli`, then type `LLEN queue:jobs`, `KEYS job:*` and `HGETALL job:<an id>`. Type `exit` to leave.
3. Harder: make jobs survive a crashing worker. Instead of `BRPOP`, use `BLMOVE` to move the ID into a list `processing:jobs`, and remove it with `LREM` when the job is done.

<details><summary>Hint for 1</summary>

Every job still has to go through llm-service, which is one container. With `DELAY_SECONDS` the fake LLM simply sleeps, so it can handle several at once, but a real model server has a limit (GPU, rate limit, cost). Adding workers beyond what the model side can handle just makes jobs wait inside llm-service instead of in the queue. Queue length and model capacity must be scaled together.
</details>

<details><summary>Solution for 3</summary>

In `worker/worker.py`, replace the `brpop` call and add a cleanup after `process()`:
```python
PROCESSING = "processing:jobs"
...
            # Take from the RIGHT of the queue and put it on the LEFT of "processing", in one atomic step.
            job_id = store.blmove(QUEUE, PROCESSING, timeout=5, src="RIGHT", dest="LEFT")
        ...
        if job_id is None:
            continue
        process(job_id)
        store.lrem(PROCESSING, 1, job_id)  # finished: remove it from "processing"
```
(Remove the `_queue_name, job_id = item` line, since `blmove` returns just the ID.) Now a crash leaves the ID in `processing:jobs`. A small "janitor" (or the worker at start-up) can move IDs whose job record is still `running` after, say, 10 minutes back to `queue:jobs`.
</details>

## Check yourself
1. Why does `POST /jobs` answer with status 202 and not 200?
2. Two workers call `BRPOP` on the same queue at the same moment. Can both get the same job?
3. What does the worker do when Docker sends SIGTERM in the middle of a job, and why does that matter?
4. Name one downside of polling, and one alternative.

<details><summary>Answers</summary>

1. 202 means "accepted, but not done yet". The work happens later in a worker; 200 would suggest the result is already in the response.
2. No. Redis runs commands one at a time, and each pop removes the item, so exactly one worker receives each job.
3. It finishes the current job, saves the result, then exits ("stopped cleanly"). Otherwise the job would be cut off half-way and stay "running" forever.
4. Polling wastes requests and adds up to one poll interval of delay. Alternatives: **webhooks** (the server calls your URL when done), **Server-Sent Events** or **WebSockets** (the server pushes the update over an open connection).
</details>

## Learn more (optional)
**Read the official docs**
- Redis lists (LPUSH, BRPOP, BLMOVE): https://redis.io/docs/latest/develop/data-types/lists/
- Redis hashes: https://redis.io/docs/latest/develop/data-types/hashes/
- redis-py (the Python client): https://redis.readthedocs.io/
- Docker Compose `--scale` (`docker compose up` reference): https://docs.docker.com/reference/cli/docker/compose/up/
- FastAPI background tasks (the simpler, in-process option, and why it's not enough for long LLM jobs): https://fastapi.tiangolo.com/tutorial/background-tasks/

**Watch**
- Hussein Nasser: [search "hussein nasser message queues"](https://www.youtube.com/results?search_query=hussein+nasser+message+queues)
- ByteByteGo: [search "bytebytego message queue explained"](https://www.youtube.com/results?search_query=bytebytego+message+queue+explained)
- Fireship: [search "fireship redis in 100 seconds"](https://www.youtube.com/results?search_query=fireship+redis+in+100+seconds)

## Next
→ [14 · Reverse proxy and API gateway](../14-reverse-proxy-and-api-gateway)
