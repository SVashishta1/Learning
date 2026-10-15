# 05 · Put your API on the internet

**What you'll build:** your to-do API from lesson 03, packed into a **container** and put online with a real link you can open on your phone and share with friends.
**Time:** ~45 min · **Builds on:** [03 · An API that saves to a database](../03-api-that-saves-to-a-database) · **Needs:** a free GitHub account and a free Render account (Option A), or Docker Desktop (Option B)

Like you're 10: until now your restaurant only existed in your bedroom. Now you rent a stall at the market, so anyone can walk up and order.

## Why this matters
Code on your laptop helps nobody else. "Deploying" (putting code on a server that's always on) is how every app reaches users, and AI models are deployed the same way: inside a container, behind an API. Docker containers are the standard way to do that at almost every tech company, and "can you deploy it?" is a common question in AI engineering interviews.

## What you'll learn
- **Deploying**: copying your app to a computer on the internet that runs it all day, so anyone can reach it.
- **Container**: a sealed box with your code plus everything it needs (Python, packages), so it runs the same everywhere.
- **Dockerfile**: the recipe that builds the box, step by step.
- **`requirements.txt`**: the list of packages your app needs, so a fresh machine can install them.
- **Port and `$PORT`**: the numbered "door" your server listens on. Hosting services tell your app which door to use.

## Before you start
- The files in this folder:
  - `main.py`: the to-do API from lesson 03, plus a home page at `/` so your bare link shows a friendly message.
  - `requirements.txt`: `fastapi` and `uvicorn[standard]`, the two packages the container installs.
  - `Dockerfile`: the recipe for the container.
- To run `main.py` on your computer without a container, the Part 1 install line is enough:
  ```bash
  pip install fastapi "uvicorn[standard]" httpx
  ```
- **Option A (Render)** needs: a free GitHub account (https://github.com/signup) and a free Render account (https://render.com). Nothing to install.
- **Option B (your computer)** needs: Docker Desktop (https://www.docker.com/products/docker-desktop/). Install it, **open it**, and wait until it says the engine is running. On Windows it may ask to install or update "WSL"; say yes and restart if asked. On Linux you can install Docker Engine instead (https://docs.docker.com/engine/install/).
- No API key needed.

## Run it
### Option A: put it online with Render (free, about 10 minutes)
1. Sign in to GitHub and **fork** this repository: open https://github.com/SVashishta1/Learning and click **Fork** (top right) → **Create fork**. You now have your own copy at `github.com/<your-name>/Learning`.
2. Go to https://render.com → **Get Started** → sign up with GitHub.
3. In the Render dashboard click **New +** (or **Add new**) → **Web Service** → connect your GitHub account if asked → pick your fork, **Learning**.
4. Fill in the form:
   - **Name:** anything, e.g. `my-todo-api` (this becomes part of your link)
   - **Language** (called **Runtime** on some screens): `Docker`
   - **Branch:** `main`
   - **Root Directory:** `ai-from-zero/part-1-apis/05-put-your-api-on-the-internet`
   - **Instance Type:** `Free`
5. Click **Deploy Web Service** (or **Create Web Service**). Render reads the `Dockerfile`, builds the container and starts it. Watch the log; after a few minutes it says **Your service is live**.
6. Open the link at the top of the page, like `https://my-todo-api.onrender.com`. Then add `/docs` to the end and add a task. 🎉

Good to know: the free plan "sleeps" after about 15 minutes without visitors, so the first visit after a break can take up to a minute. Tasks reset whenever it restarts or redeploys, because the free plan's disk isn't permanent.

### Option B: run the container on your own computer
1. Make sure Docker Desktop is open and running.
2. From the course folder (`ai-from-zero`):
   ```bash
   cd part-1-apis/05-put-your-api-on-the-internet
   docker build -t my-todo-api .
   docker run -p 8000:8000 my-todo-api
   ```
   `docker build` follows the Dockerfile to make an **image** (the packed box) named `my-todo-api`. The `.` at the end means "the recipe and files are in this folder". `docker run` starts a container from it.
3. Open http://localhost:8000 and http://localhost:8000/docs
4. Stop it with **Ctrl + C** in the terminal.

### What you should see
`docker build` prints its steps and ends with lines like:
```
 => [5/5] COPY main.py .
 => exporting to image
 => => naming to docker.io/library/my-todo-api:latest
```
`docker run` then shows:
```
INFO:     Started server process [1]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```
In the browser, the home page (on your computer or your Render link):
```
{"message":"My to-do API is live! Add /docs to the end of this link to try it."}
```
and adding a task in `/docs` returns `{"id": 1, "title": "ship it", "done": 0}`. On Render, the same `Uvicorn running on http://0.0.0.0:...` line appears in the **Logs** tab, with Render's own port number.

## How it works
```
Dockerfile ──docker build──▶ image (Python 3.12 + packages + main.py) ──docker run──▶ container running uvicorn
                                                                                        │
browser / phone ──▶ https://my-todo-api.onrender.com ──▶ Render ──▶ port $PORT ──────────┘
```
Read the `Dockerfile` top to bottom. Each line is one step of the recipe:
1. `FROM python:3.12-slim` starts from a small Linux system that already has Python 3.12.
2. `WORKDIR /app` makes `/app` the working folder inside the box.
3. `COPY requirements.txt .` then `RUN pip install --no-cache-dir -r requirements.txt` copies the package list in and installs it. `-r` means "read the list from this file". Doing this before copying your code lets Docker reuse this slow step when only your code changes.
4. `COPY main.py .` copies your code in.
5. `CMD [...]` is the command the box runs when it starts: `uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}`.
   - `--host 0.0.0.0` means "accept visitors from outside this box". The default, `127.0.0.1`, would only accept visitors from inside the container, so nobody could reach it.
   - `${PORT:-8000}` means "use the `PORT` setting if there is one, otherwise 8000". Render sets `PORT` for you; on your computer it falls back to 8000.
   - `exec` makes uvicorn the main program of the box, so Ctrl + C reaches it and stops the container cleanly.
6. In `docker run -p 8000:8000`, `-p` connects a door on your computer (first number) to a door in the container (second number).

`main.py` is lesson 03's code with one addition: `home()` at `/`, because people usually open the bare link first, and `{"detail":"Not Found"}` would look broken.

## If something goes wrong
- **`Cannot connect to the Docker daemon` / `error during connect` / `docker: command not found`** → Docker Desktop isn't installed or isn't running. Open it and wait until it's ready, then run the command again in a **new** terminal.
- **`Bind for 0.0.0.0:8000 failed: port is already allocated`** → something else uses port 8000 (maybe a `uvicorn` from an earlier lesson). Stop it, or use another door on your side: `docker run -p 8001:8000 my-todo-api` and open http://localhost:8001.
- **`failed to read dockerfile` / `open Dockerfile: no such file or directory`** → you're not in the lesson folder. `cd part-1-apis/05-put-your-api-on-the-internet` first; the `.` at the end of `docker build` matters too.
- **Render build fails with "no such file" or can't find the Dockerfile** → the **Root Directory** is wrong. It must be exactly `ai-from-zero/part-1-apis/05-put-your-api-on-the-internet` (no leading `/`). Fix it under **Settings** and click **Manual Deploy → Deploy latest commit**.
- **Your Render link is slow or shows a loading page** → the free service was asleep. Wait up to a minute and refresh.

## Try this
1. Run the container on a different door of your computer: `docker run -p 9000:8000 my-todo-api`, then open http://localhost:9000/docs. Which number did you change, and why not the other one?
2. Change the home page message in `main.py` and get the new version running. (Local: rebuild and run. Render: change the file in your fork on GitHub.)
3. Add the `GET /tasks/done` endpoint from lesson 03's **Try this** to this `main.py`, rebuild, and test it in `/docs`.

<details><summary>Hints and solutions</summary>

1. You changed the first number (your computer's door). The second number is the door inside the container, which is still 8000 because that's what uvicorn listens on.
2. Local: after saving `main.py`, run `docker build -t my-todo-api .` again, then `docker run -p 8000:8000 my-todo-api`. The container only has the code from when it was built. Render: open `main.py` in your fork on github.com, click the **pencil** icon, edit the message, click **Commit changes**. Render notices the new commit and redeploys by itself in a few minutes.
3. Add this to `main.py`, then rebuild and run as in hint 2:
   ```python
   @app.get("/tasks/done")
   def done_tasks():
       rows = db.execute("SELECT * FROM tasks WHERE done = 1").fetchall()
       return [dict(row) for row in rows]
   ```
</details>

## Check yourself
1. What is the difference between an image and a container?
2. Why does the `CMD` use `--host 0.0.0.0` instead of the default?
3. Your Render app restarted and the tasks are gone. Why, when lesson 03 kept them after a restart?
4. Why copy `requirements.txt` and install packages *before* copying `main.py`?

<details><summary>Answers</summary>

1. An image is the packed box, built once from the Dockerfile (like a recipe that's been cooked and frozen). A container is a running copy of that image. You can start many containers from one image.
2. `127.0.0.1` only accepts visitors from inside the same machine, which here means inside the container. `0.0.0.0` accepts visitors from outside, like your browser or Render.
3. `tasks.db` lives inside the container. A new container starts from the image, which has no `tasks.db`, and Render's free plan has no permanent disk. Real apps keep data in a separate database service for this reason.
4. Docker caches each step. If only your code changes, it reuses the slow "install packages" step and rebuilds in seconds.
</details>

## Learn more (optional)
- Docker's official "Get started" guide: https://docs.docker.com/get-started/
- Render's guide to deploying with Docker: https://render.com/docs/docker
- FastAPI in containers: https://fastapi.tiangolo.com/deployment/docker/
- Video: search YouTube for "Docker in 100 seconds" or "Docker tutorial for beginners".

## Next
→ [Part 2 · Machine learning: 06 · Predict house prices](../../part-2-machine-learning/06-predict-house-prices) (see the [Part 2 overview](../../part-2-machine-learning) for its install line)
