# 1.7 · Dockerize & deploy to the cloud

**What you'll build:** you pack the login + to-do API from 1.6 (copied into `app/`) into a **Docker container**, run it next to a real PostgreSQL database with one command, then put it **on the internet** with a public URL.
**Like you're 10:** Docker is a lunchbox. You pack the food (code), the fork (Python) and the napkin (packages) together, so it works the same at school, at grandma's, or in the cloud.
**Time:** ~2 h · **Builds on:** [1.6 · Login API](../06-login-api-hashed-passwords-and-jwt) · **Needs:** Docker Desktop (Part A), a free GitHub account and a free Render account (Part B)

## Why this matters
"It works on my machine" is not a product. Companies ship almost every backend, including AI model servers, as Docker images, and deploy them to cloud platforms that read configuration from environment variables. After this project you'll have a real public URL to show people, and the same Dockerfile pattern will carry your AI apps in Levels 4 and 7.

## What you'll learn
- **Image vs container:** an image is the packed lunchbox (frozen recipe result); a container is one running copy of it.
- **Dockerfile and layer caching:** step-by-step build instructions; copying `requirements.txt` before the code makes rebuilds fast.
- **Docker Compose:** one file that starts several containers (API + database) and wires them together.
- **12-factor config:** the same image runs everywhere; only environment variables (`DATABASE_URL`, `SECRET_KEY`, `PORT`) change.
- **Deploying:** a platform builds your image from GitHub, gives it a database and a URL, and checks `/health`.

## Before you start
- **Docker Desktop**: https://www.docker.com/products/docker-desktop/ (start it, and wait until it says "Engine running"). Check with `docker --version`.
- To run the tests **without** Docker: `pip install -r requirements.txt` from this folder (it installs `app/requirements.txt`: the same packages as 1.6).
- For Part B: a GitHub account and a Render account (sign up at https://render.com with GitHub and choose the free plan).
- No API key needed.

What's in this folder:
```
07-dockerize-and-deploy-to-the-cloud/
├── app/                  ← the 1.6 app (main.py, security.py, test_main.py, requirements.txt)
├── Dockerfile            ← how to build the image
├── .dockerignore         ← files NOT to copy into the image
├── docker-compose.yml    ← API + Postgres together, for your laptop
└── render.yaml           ← API + Postgres together, for Render's cloud
```

## Run it
### Part A: run it in Docker on your computer
1. Build and start everything:
   ```bash
   cd level-1-apis/07-dockerize-and-deploy-to-the-cloud
   docker compose up --build
   ```
   The first build downloads Python and Postgres images (a few minutes). Later builds take seconds.
2. Open http://localhost:8000/docs. It's the same API as 1.6, now inside a container and talking to Postgres. Sign up, authorize, add a todo.
3. Stop with `Ctrl+C`, then `docker compose down`. Add `-v` (`docker compose down -v`) to also delete the database data.

Useful commands (in a second terminal while it runs):
```bash
docker ps                                                      # what's running
docker compose logs -f api                                     # watch the API's logs
docker compose exec db psql -U app -c "select * from users;"   # look inside Postgres
docker compose run --rm api pytest -q                          # run the tests inside the container
```

### Part B: deploy to Render (free)
1. **Put the code in your own GitHub account.** On https://github.com/SVashishta1/Learning click **Fork** (Render can only deploy repos you own). If you made your own repo instead, push this course into it.
2. Go to https://dashboard.render.com and sign in with GitHub.
3. Click **New → Blueprint**, connect your fork, and when asked for the **Blueprint path**, enter:
   `ai-engineer-journey/level-1-apis/07-dockerize-and-deploy-to-the-cloud/render.yaml`
4. Render shows what it will create: a web service `login-todo-api` and a database `login-todo-db`, both on the free plan. Click **Deploy Blueprint** (called **Apply** on some screens).
5. Wait for the build (about 3 to 5 minutes; watch the **Logs** tab). When it says **Live**, your URL is at the top, like `https://login-todo-api-abcd.onrender.com`.
6. Open `<your URL>/health`, then `<your URL>/docs`, and sign up from your phone! 🎉

Render free plan facts (check https://render.com/pricing for the latest):
- A free web service **sleeps after 15 minutes** without visitors; the next request wakes it, which takes about a minute.
- A free Postgres database is small (1 GB) and **expires 30 days after you create it**, unless you upgrade. Fine for learning; don't keep real data there.

**Other platforms** (all work with the same Dockerfile because it listens on `$PORT`):
- **Railway** (https://railway.com): **New Project → Deploy from GitHub repo** → pick your fork. In the service's **Settings → Source**, set **Root Directory** to `ai-engineer-journey/level-1-apis/07-dockerize-and-deploy-to-the-cloud` (Railway then finds the Dockerfile). Add a database with **+ Create → Database → PostgreSQL**. In the API service's **Variables**, add `DATABASE_URL` = `${{Postgres.DATABASE_URL}}` and `SECRET_KEY` = a long random string, then **Settings → Networking → Generate Domain**. Railway gives new accounts a trial credit, then charges by usage (a few dollars a month for this app).
- **Fly.io** (https://fly.io): install `flyctl`, run `fly launch` in this folder (it detects the Dockerfile), and `fly postgres create`. Fly.io needs a credit card and bills by usage; there's no free plan for new accounts.

### What you should see
Part A, `docker compose up --build` ends with:
```
 ✔ Container 07-dockerize-and-deploy-to-the-cloud-db-1   Healthy
 ✔ Container 07-dockerize-and-deploy-to-the-cloud-api-1  Started
api-1  | INFO:     Started server process [1]
api-1  | INFO:     Waiting for application startup.
api-1  | INFO:     Application startup complete.
api-1  | INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
api-1  | INFO:     172.18.0.1:42554 - "GET /health HTTP/1.1" 200 OK
api-1  | INFO:     172.18.0.1:42568 - "POST /signup HTTP/1.1" 201 Created
```
`docker compose run --rm api pytest -q` prints `6 passed`. On Render, `<your URL>/health` answers:
```
{"status":"ok"}
```
The API waits until the database is **Healthy** before starting: that's the `depends_on ... condition: service_healthy` line doing its job.

## How it works
```
your laptop:  docker compose ──► builds image from Dockerfile ──► container "api" ──DATABASE_URL──► container "db" (Postgres)
the cloud:    git push ──► Render reads render.yaml ──► builds the same Dockerfile ──► service + free Postgres ──► https URL
```
1. **`Dockerfile`**, line by line:
   - `FROM python:3.12-slim`: start from a small Linux image with Python installed.
   - `ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1`: no `.pyc` clutter, and logs appear immediately.
   - `WORKDIR /code`: all following commands run in `/code` inside the image.
   - `COPY app/requirements.txt .` then `RUN pip install ...`: install packages *before* copying the code. Docker caches each step (a **layer**), so editing `main.py` doesn't reinstall everything.
   - `COPY app/ .`: now copy the code (`.dockerignore` keeps out `__pycache__`, `*.db`, `.venv` and `.env`).
   - `ENV PORT=8000` and `CMD ["sh", "-c", "exec uvicorn main:app --host 0.0.0.0 --port ${PORT}"]`: start the server. `--host 0.0.0.0` accepts connections from outside the container (the default `127.0.0.1` would only accept connections from inside it). Cloud platforms set their own `PORT` (Render uses 10000), and `${PORT}` picks it up.
2. **`docker-compose.yml`** defines two services. `db` runs the official `postgres:16` image with user/password/database `app`, a `healthcheck` (`pg_isready`), and a named volume `pgdata` so data survives restarts. `api` is built from the Dockerfile, publishes port 8000, and gets `DATABASE_URL=postgresql+psycopg://app:app@db:5432/app`: inside Compose's network, the hostname `db` *is* the database container.
3. **`render.yaml`** (a Render "Blueprint") describes the same thing for the cloud: a `web` service with `runtime: docker`, `rootDir` pointing at this folder (the repo has many projects), `healthCheckPath: /health`, a `SECRET_KEY` that Render generates, and `DATABASE_URL` copied from the free database's `connectionString`. `ipAllowList: []` means only your Render services can reach the database.
4. **`app/main.py`** is the 1.6 code. The one detail that matters for the cloud is `fix_db_url()`: Render and Railway hand out URLs starting with `postgresql://` or `postgres://`, and `fix_db_url` rewrites them to `postgresql+psycopg://` so SQLAlchemy uses the psycopg 3 driver we installed. `/health` returns `{"status": "ok"}` so the platform knows the app is alive.

## If something goes wrong
- **`Cannot connect to the Docker daemon`** or **`error during connect`** → Docker Desktop isn't running. Start it and wait for "Engine running".
- **`Bind for 0.0.0.0:8000 failed: port is already allocated`** → something else (maybe uvicorn from 1.6) uses port 8000. Stop it, or change `"8000:8000"` to `"8001:8000"` in `docker-compose.yml` and open http://localhost:8001.
- **You changed code but the container runs the old version** → you need `--build`: `docker compose up --build`.
- **Render build fails with `failed to read dockerfile` / `no such file`** → the Blueprint path or `rootDir` doesn't match your repo. If your fork has the course at a different place (for example you copied this folder to the root of a new repo), change `rootDir` in `render.yaml` to that folder (or delete the line if it's the repo root), commit, push, and redeploy. Or skip the Blueprint: **New → Web Service** (pick your repo, Language **Docker**, Root Directory = this folder, Instance Type **Free**), then **New → Postgres** (Free), copy its **Internal Database URL** into the web service's `DATABASE_URL` environment variable, and add a `SECRET_KEY` variable.
- **The Render URL is very slow or times out on the first visit** → the free service was asleep. Wait about a minute and refresh.

## Try this
1. Add `GET /version` that returns the environment variable `APP_VERSION`, set it in `docker-compose.yml`, and rebuild.
   <details><summary>Solution</summary>

   In `app/main.py`:
   ```python
   @app.get("/version")
   def version():
       return {"version": os.getenv("APP_VERSION", "dev")}
   ```
   In `docker-compose.yml`, under `api: environment:` add `APP_VERSION: "1.0.0"`. Run `docker compose up --build` and open http://localhost:8000/version → `{"version":"1.0.0"}`. On Render, add `APP_VERSION` under **Environment** and it redeploys with the new value: same image, different config.
   </details>
2. Run the tests inside the container, then make one fail on purpose (change an expected status code in `app/test_main.py`) and run them again.
   <details><summary>Hint</summary>

   `docker compose run --rm api pytest -q`. The test files are inside the image, so after editing you must rebuild (`docker compose build api`) before the failure shows up. That's the image being a frozen snapshot.
   </details>
3. Make the image smaller: compare `docker images` before and after changing the first line to `FROM python:3.12-alpine`. Does bcrypt still install?
   <details><summary>Answer</summary>

   Yes: bcrypt and psycopg-binary publish ready-made wheels for Alpine Linux, so nothing has to compile. In our test the image went from about 320 MB (slim) to about 220 MB (alpine), and all tests still passed. Smaller images upload and start faster, but Alpine uses a different C library (musl), which occasionally breaks packages that ship no Alpine wheel; `-slim` is the safer default.
   </details>

## Check yourself
1. What's the difference between an image and a container?
2. Why does the Dockerfile copy `requirements.txt` and run `pip install` *before* copying the code?
3. Inside Docker Compose, why is the database host `db` and not `localhost`?
4. The same image runs on your laptop and on Render. What changes between the two, and how does the app find out?

<details><summary>Answers</summary>

1. An image is a read-only package (code + Python + packages). A container is a running instance of an image; you can run many containers from one image.
2. Docker caches each step. If only the code changed, the cached "install packages" layer is reused, so rebuilds take seconds instead of minutes.
3. Each container has its own `localhost` (itself). Compose puts the services on a shared network where each service's name works as a hostname, so `db` reaches the Postgres container.
4. Configuration: `DATABASE_URL`, `SECRET_KEY` and `PORT`. The app reads them from environment variables with `os.getenv`, which Compose and Render set for it.
</details>

## Learn more (optional)
- Docker in 100 seconds (Fireship): https://www.youtube.com/watch?v=Gjnup-PuquQ
- Docker tutorial for beginners (TechWorld with Nana): https://www.youtube.com/watch?v=3c-iBn73dDE
- FastAPI in containers: https://fastapi.tiangolo.com/deployment/docker/
- Render Blueprint reference: https://render.com/docs/blueprint-spec
- The Twelve-Factor App (config): https://12factor.net/config

## Next
→ [1.8 · Weather proxy: calling other APIs](../08-weather-proxy-calling-other-apis)
