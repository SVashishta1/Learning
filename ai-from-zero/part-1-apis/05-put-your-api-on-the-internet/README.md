# 05 · Put your API on the internet

**What it does:** takes your to-do API from project 03 and puts it online with a real link you can open on your phone.

## Option A: Render (free, no installs, about 10 minutes)
1. Make a free GitHub account and **fork** this repository: click "Fork" at https://github.com/SVashishta1/Learning.
2. Go to https://render.com → sign up with GitHub → **New +** → **Web Service** → pick your fork.
3. Fill in:
   - **Root Directory:** `ai-from-zero/part-1-apis/05-put-your-api-on-the-internet`
   - **Runtime:** Docker
   - **Instance type:** Free
4. Click **Create Web Service**. Wait for "Live", then open `https://<your-name>.onrender.com/docs`. 🎉

(The free plan sleeps when unused, so the first visit can take ~30 seconds to wake up. Tasks reset when it restarts, because the free disk isn't permanent.)

## Option B: run the container on your computer
1. Install Docker Desktop: https://www.docker.com/products/docker-desktop/
2. Run:
   ```bash
   cd part-1-apis/05-put-your-api-on-the-internet
   docker build -t my-todo-api .
   docker run -p 8000:8000 my-todo-api
   ```
3. Open http://localhost:8000/docs

## The idea in one sentence
A **Dockerfile** is a recipe that packs your code and everything it needs into a box (a container), so it runs the same on your laptop and in the cloud.

## Try this
- Send your Render link to a friend and ask them to add a task. You've shipped your first web service!
