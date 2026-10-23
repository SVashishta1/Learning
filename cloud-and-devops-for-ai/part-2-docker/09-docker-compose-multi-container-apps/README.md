# 09 · Docker Compose: multi-container apps

**What you'll build:** the Mood API grown up: the API container plus a **Postgres** database that keeps a history of every prediction and a **Redis** cache that answers repeated questions instantly. All three start with **one command**, in the right order, on their own private network, described in one `compose.yaml` file.
**Like you're 5:** each container is one musician. Docker Compose is the conductor with the sheet music (`compose.yaml`): it tells everyone when to start, who sits next to whom, and waits until the drummer is ready before the singer begins.
**Time:** ~75 min · **Builds on:** [08 · Smaller, safer images](../08-smaller-safer-images) · **Needs:** Docker with Compose v2 (`docker compose version`)

## Why this matters
Real AI apps are never one container. A typical RAG or chatbot API needs a database (users, history, vectors), a cache (to avoid paying for the same LLM answer twice), maybe a queue and a local model server. Typing three long `docker run` commands in the right order, with the right networks and volumes, every time, is error-prone. Compose writes it all down once, in a file that lives in Git, so anyone can start the whole system with `docker compose up`. It is the standard way to run multi-service apps on a laptop, in CI, and on small servers.

## What you'll learn
- **compose.yaml:** a YAML file listing **services** (containers), **volumes** and **networks**, replacing long `docker run` commands.
- **Service names are addresses:** inside the Compose network, the API reaches the database at the host name `db` and the cache at `cache`.
- **Start-up order with health checks:** `depends_on` + `condition: service_healthy` makes the API wait until Postgres and Redis really answer, not just until their containers exist.
- **Private networks:** only the API publishes a port; the database and cache are unreachable from outside.
- **The Compose life cycle:** `up`, `ps`, `logs`, `exec`, `stop`/`start`, `down`, and `down -v`.

## Before you start
- Docker running; `docker compose version` prints `Docker Compose version v2...` or newer. (The old `docker-compose` with a dash is Compose v1, which is retired; use `docker compose` with a space.)
- No pip install on your computer: the API image installs its own packages (`fastapi`, `uvicorn`, `psycopg[binary]` to talk to Postgres, `redis` to talk to Redis).
- No API key. You choose a database password in Step 2.
- Port **8000** free on your computer.

**Files in this folder**

| File | What it is |
|------|------------|
| `compose.yaml` | the whole system: 3 services, 1 volume, 1 network (dissected below) |
| `main.py` | the API: `/predict` (with cache + history), `/history`, `/health` |
| `requirements.txt` | the API's packages |
| `Dockerfile`, `.dockerignore` | the production Dockerfile pattern from lesson 08 |
| `.env.example` | a template for your settings; you copy it to `.env` |
| `.gitignore` | keeps `.env` (your real password) out of Git |

## Run it
From the course folder (`cloud-and-devops-for-ai`):
```bash
cd part-2-docker/09-docker-compose-multi-container-apps
```

### Step 1 · Try to start without settings (to see the safety net)
```bash
docker compose up -d
```
You should see:
```
error while interpolating services.api.environment.DATABASE_URL: required variable POSTGRES_PASSWORD is missing a value: Copy .env.example to .env first
```
`compose.yaml` refuses to start without a password, and the message tells you what to do.

### Step 2 · Create your .env file
```bash
cp .env.example .env
nano .env
```
Change `change-me-please` to a password of your own, save (**Ctrl + O**, **Enter**) and exit (**Ctrl + X**). Compose reads `.env` from this folder automatically. It is in `.gitignore`, so it never reaches GitHub.

### Step 3 · Build and start everything
```bash
docker compose up -d --build
```
| Piece | Meaning |
|-------|---------|
| `docker compose` | the Compose tool. It reads `compose.yaml` in the current folder. |
| `up` | create and start everything the file describes (networks, volumes, containers) |
| `-d` | detached: in the background (like `docker run -d`) |
| `--build` | build the `api` image from the Dockerfile first (otherwise Compose reuses an old build) |

You should see (after the build lines):
```
 Volume mood-compose_pgdata Created
 Network mood-compose_backend Created
 Container mood-compose-db-1 Created
 Container mood-compose-cache-1 Created
 Container mood-compose-api-1 Created
 Container mood-compose-cache-1 Started
 Container mood-compose-db-1 Started
 Container mood-compose-db-1 Waiting
 Container mood-compose-cache-1 Waiting
 Container mood-compose-cache-1 Healthy
 Container mood-compose-db-1 Healthy
 Container mood-compose-api-1 Starting
 Container mood-compose-api-1 Started
```
Look at the order: the database and cache start first, Compose **waits** until both are `Healthy`, and only then starts the API. Every name starts with `mood-compose`, the project name from the file.

### Step 4 · Check the services
```bash
docker compose ps
```
Wait about 15 seconds (the API's own health check needs a moment) and run it again. You should see:
```
NAME                   IMAGE              SERVICE   STATUS                    PORTS
mood-compose-api-1     mood-compose-api   api       Up 17 seconds (healthy)   0.0.0.0:8000->8000/tcp
mood-compose-cache-1   redis:7-alpine     cache     Up 29 seconds (healthy)   6379/tcp
mood-compose-db-1      postgres:16        db        Up 29 seconds (healthy)   5432/tcp
```
(Some columns trimmed.) Only the API has `0.0.0.0:8000->`: it is the only door to the outside. `5432/tcp` and `6379/tcp` without an arrow mean "open inside the network only".

### Step 5 · Use the app
```bash
curl -s localhost:8000/health
curl -s -X POST localhost:8000/predict -H "Content-Type: application/json" -d '{"text": "I love this great app"}'
curl -s -X POST localhost:8000/predict -H "Content-Type: application/json" -d '{"text": "I love this great app"}'
curl -s -X POST localhost:8000/predict -H "Content-Type: application/json" -d '{"text": "The wifi is broken again"}'
curl -s localhost:8000/history
```
You should see:
```
{"status":"ok","database":"ok","cache":"ok"}
{"text":"I love this great app","label":"positive","score":2,"cached":false}
{"text":"I love this great app","label":"positive","score":2,"cached":true}
{"text":"The wifi is broken again","label":"negative","score":-1,"cached":false}
[{"id":3,"text":"The wifi is broken again","label":"negative","created_at":"2026-10-22T04:14:58.606694+00:00"},{"id":2,"text":"I love this great app","label":"positive","created_at":"..."},{"id":1,"text":"I love this great app","label":"positive","created_at":"..."}]
```
The second identical question says `"cached":true`: the answer came from Redis. Every question is stored in Postgres, newest first in `/history`.

### Step 6 · Read logs and look inside the helpers
```bash
docker compose logs api
docker compose exec cache redis-cli keys '*'
docker compose exec db psql -U mood -d mood -c "SELECT id, text, label FROM predictions;"
```
| Piece | Meaning |
|-------|---------|
| `docker compose logs api` | the logs of the `api` service (leave out `api` for all services; add `-f` to follow live) |
| `docker compose exec cache ...` | run a command in the running `cache` service (like `docker exec`, but by service name) |
| `redis-cli keys '*'` | Redis's own client: list every key (`*` = any). Fine for practice; never on a big production Redis. |
| `psql -U mood -d mood -c "..."` | Postgres's client: user `mood`, database `mood`, run this SQL |

You should see:
```
api-1  | INFO:     Application startup complete.
api-1  | INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
api-1  | INFO:     172.19.0.1:48506 - "POST /predict HTTP/1.1" 200 OK
...
mood:the wifi is broken again
mood:i love this great app
 id |           text           |  label
----+--------------------------+----------
  1 | I love this great app    | positive
  2 | I love this great app    | positive
  3 | The wifi is broken again | negative
(3 rows)
```

### Step 7 · See that service names are addresses
```bash
docker compose exec api python -c "import socket; print('db ->', socket.gethostbyname('db')); print('cache ->', socket.gethostbyname('cache'))"
```
You should see two private addresses, for example:
```
db -> 172.19.0.3
cache -> 172.19.0.2
```
Compose's network has a built-in phone book (DNS): the name `db` always finds the database container, whatever its address is today. That's why `compose.yaml` can say `@db:5432` and `redis://cache:6379`.

### Step 8 · Stop everything, start again: the data survives
```bash
docker compose down
docker volume ls
docker compose up -d
```
Wait until `docker compose ps` shows the API as `healthy`, then:
```bash
curl -s "localhost:8000/history?limit=1"
```
You should see:
```
 Container mood-compose-api-1 Removed
 Container mood-compose-db-1 Removed
 Container mood-compose-cache-1 Removed
 Network mood-compose_backend Removed
DRIVER    VOLUME NAME
local     mood-compose_pgdata
...
[{"id":3,"text":"The wifi is broken again","label":"negative","created_at":"..."}]
```
`down` removed the containers and the network but **kept** the named volume, so the history is still there. (The Redis cache started empty again: it only lives in memory, which is fine for a cache.)

### Step 9 · Remove everything, including the data
```bash
docker compose down -v
```
`-v` also removes the **v**olumes declared in the file. The database is gone for good. Use it when you want a clean start.

### What you should see
- `docker compose ps`: three services, all `(healthy)`, only `api` with a published port.
- `/predict` answers `"cached":false` the first time and `"cached":true` for the same text again.
- `/history` still has old rows after `down` + `up`, and is empty after `down -v` + `up`.

## How it works
```mermaid
flowchart LR
    U["You<br/>(curl / browser)"] -- "localhost:8000" --> A
    subgraph N["network: mood-compose_backend (private)"]
        A["api<br/>FastAPI :8000"] -- "redis://cache:6379" --> C["cache<br/>Redis :6379"]
        A -- "postgresql://...@db:5432" --> D["db<br/>Postgres :5432"]
    end
    D --- V[("volume<br/>pgdata")]
```
**Request path:** `POST /predict` → `main.py` builds a key like `mood:i love this great app` → asks Redis `GET` → if found, returns it with `cached: true`; if not, runs `predict_mood()`, stores the answer in Redis with `SET ... ex=3600` (expires after an hour) → in both cases inserts a row into the `predictions` table in Postgres → returns JSON.

### The app (`main.py`)
1. `DATABASE_URL` and `REDIS_URL` come from environment variables that `compose.yaml` sets. The defaults (`localhost`) are only for running the app outside Docker.
2. `lifespan()` runs once at start-up and creates the `predictions` table if it doesn't exist (`CREATE TABLE IF NOT EXISTS`). `SERIAL` = an auto-numbered ID, `TIMESTAMPTZ ... DEFAULT now()` = the time, filled in automatically.
3. `with psycopg.connect(DATABASE_URL) as conn:` opens a connection and **commits** (saves) the changes when the block ends. `%s` placeholders send user text separately from the SQL, which prevents SQL injection.
4. `cache.get(key)` / `cache.set(key, json.dumps(result), ex=CACHE_SECONDS)`: Redis stores text, so results are turned into JSON text and back.
5. `/health` really talks to both helpers (`SELECT 1` and `PING`), so it fails if either is down. The Dockerfile's `HEALTHCHECK` calls it.

### compose.yaml, key by key
| Key | Meaning |
|-----|---------|
| `name: mood-compose` | the **project** name. Compose puts it in front of every container (`mood-compose-api-1`), network and volume name. Without it, the folder name is used. |
| `services:` | the list of containers to run. Each key below it (`api`, `db`, `cache`) is a **service name** and also its host name on the network. |
| `build: .` | build this service's image from the Dockerfile in `.` (this folder) |
| `image: postgres:16` | use a ready-made image instead of building one |
| `ports:` / `- "8000:8000"` | publish a port, `HOST:CONTAINER`, like `-p`. Quoted, because YAML can misread some `xx:yy` numbers. |
| `environment:` | environment variables, like `-e`. Written as `KEY: value` pairs. |
| `${POSTGRES_PASSWORD:?Copy .env.example to .env first}` | **interpolation**: Compose replaces it with the variable's value from `.env` (or your shell). `:?message` = if it's missing or empty, stop with this error. (`${VAR:-default}` would use a default instead.) |
| `postgresql://mood:...@db:5432/mood` | a database address: `scheme://user:password@host:port/database`. The host is `db`, the service name. |
| `depends_on:` | start these services first |
| `condition: service_healthy` | ...and wait until their health check passes, not just until they've started |
| `networks:` / `- backend` | attach the service to the network called `backend` |
| `restart: unless-stopped` | if the container crashes (or the computer reboots), start it again, unless you stopped it yourself |
| `volumes:` / `- pgdata:/var/lib/postgresql/data` (in a service) | mount the named volume `pgdata` where Postgres keeps its files, like `-v` |
| `healthcheck:` | how Docker checks this service is OK (like the Dockerfile `HEALTHCHECK`, but in Compose) |
| `test: ["CMD-SHELL", "pg_isready -U mood -d mood"]` | the check. `CMD-SHELL` = run the text through a shell. `pg_isready` is Postgres's own "are you ready?" tool. |
| `test: ["CMD", "redis-cli", "ping"]` | `CMD` = run this program directly (no shell). Redis answers `PONG` when ready. |
| `interval: 5s` / `timeout: 3s` / `retries: 10` | check every 5 s, fail a check after 3 s, call it unhealthy after 10 failures in a row |
| `volumes:` / `pgdata:` (top level) | declare the named volume. Compose creates it as `mood-compose_pgdata`. |
| `networks:` / `backend:` (top level) | declare the network. Compose creates it as `mood-compose_backend`, with the service-name phone book built in. |

(Compose always makes a `default` network even if you don't write one. Naming it `backend` makes the design visible, and lets you add, for example, a `frontend` network later so a web UI can reach the API but not the database.)

**Why `depends_on` needs `service_healthy`:** Postgres's container "starts" in a second, but the database inside needs several more seconds to initialise. Without the condition, the API would start, try to create its table, find nothing listening, and crash. The health check turns "container started" into "database ready".

## If something goes wrong
- **`required variable POSTGRES_PASSWORD is missing a value`** → you haven't created `.env`. Run `cp .env.example .env` in this folder.
- **`password authentication failed for user "mood"` in `docker compose logs api`** → you changed the password in `.env` **after** the database volume was first created; Postgres only reads `POSTGRES_PASSWORD` the very first time. For practice data, reset with `docker compose down -v` and `docker compose up -d --build`.
- **`Bind for 0.0.0.0:8000 failed: port is already allocated`** → another container (maybe `mood` from lesson 08) uses 8000. Stop it with `docker rm -f mood`, or change the API's ports line to `"8001:8000"`.
- **`dependency failed to start: container mood-compose-db-1 is unhealthy`** → the database never became ready. Read `docker compose logs db`. Common causes: no disk space, or an old, broken volume (fix with `docker compose down -v`).
- **You changed `main.py` but the API still behaves the old way** → `up -d` alone reuses the old image. Use `docker compose up -d --build`.

## Try this
1. Stop only the cache with `docker compose stop cache`, call `/health` and `/predict`, read the API logs, then `docker compose start cache` and call `/health` again.
2. Connect to the database from a **one-off** container on the same network, without publishing port 5432.
3. Make the cache time configurable: read `CACHE_SECONDS` from an environment variable (default 3600) and set it to 60 in `compose.yaml`.

<details><summary>Hints and solutions</summary>

1. ```bash
   docker compose stop cache
   curl -s -w " HTTP %{http_code}\n" localhost:8000/health
   docker compose logs api | tail -3
   docker compose start cache
   curl -s localhost:8000/health
   ```
   With the cache stopped you get `Internal Server Error HTTP 500` (`-w " HTTP %{http_code}\n"` makes curl print the status code), and the log shows `redis.exceptions.ConnectionError: Error -2 connecting to cache:6379. Name or service not known.`: a stopped container also disappears from the network's phone book. After `start`, health is `ok` again. In Part 3 (lesson 15) you'll make apps survive this gracefully.
2. ```bash
   docker run --rm -it --network mood-compose_backend -e PGPASSWORD=<your password> postgres:16 psql -h db -U mood -d mood -c "SELECT count(*) FROM predictions;"
   ```
   `--network mood-compose_backend` puts the temporary container on the app's private network, so the name `db` works; `PGPASSWORD` gives `psql` the password; `-h db` = the host.
3. In `main.py` change the line to `CACHE_SECONDS = int(os.getenv("CACHE_SECONDS", "3600"))` (environment variables are always text, so `int()` turns it into a number). In `compose.yaml`, under the `api` service's `environment:`, add `CACHE_SECONDS: "60"`. Then `docker compose up -d --build`. Check with `docker compose exec cache redis-cli ttl "mood:i love this great app"` after a new prediction: the time left is at most 60.
</details>

## Check yourself
1. How does the API find the database, without knowing its IP address?
2. What is the difference between `depends_on: [db]` and `depends_on: db: condition: service_healthy`?
3. Why do `db` and `cache` have no `ports:` section?
4. What is the difference between `docker compose down` and `docker compose down -v`?

<details><summary>Answers</summary>

1. By its service name: `db`. Compose's network has built-in DNS that turns service names into the containers' current addresses.
2. The first only waits until the db **container has started**; the second waits until its **health check passes**, meaning Postgres is really ready to accept connections.
3. Only the API needs to be reached from outside. Keeping the database and cache private (reachable only on the Compose network) is safer: nobody outside can try to log in to them.
4. `down` removes containers and networks but keeps named volumes (your data). `down -v` also deletes the volumes, so the data is gone.
</details>

## Learn more (optional)
**Read the official docs**
- Docker Compose overview: https://docs.docker.com/compose/
- The Compose file reference (every key): https://docs.docker.com/reference/compose-file/
- Control start-up order (`depends_on`, health checks): https://docs.docker.com/compose/how-tos/startup-order/
- Networking in Compose: https://docs.docker.com/compose/how-tos/networking/
- Variable interpolation and `.env`: https://docs.docker.com/compose/how-tos/environment-variables/variable-interpolation/
- Official images: https://hub.docker.com/_/postgres · https://hub.docker.com/_/redis
- Psycopg 3 (Postgres from Python): https://www.psycopg.org/psycopg3/docs/ · Redis Python client: https://redis.readthedocs.io/

**Watch**
- TechWorld with Nana, Docker Compose tutorial: https://www.youtube.com/results?search_query=techworld+with+nana+docker+compose+tutorial
- Fireship, Docker Compose in 100 seconds: https://www.youtube.com/results?search_query=fireship+docker+compose
- FastAPI + Postgres + Redis with Docker Compose: https://www.youtube.com/results?search_query=fastapi+postgres+redis+docker+compose

## Next
→ [10 · Local LLMs in Docker](../10-local-llms-in-docker)
