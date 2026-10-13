# 1.7 · Dockerize & deploy to the cloud

**What you build:** you pack the login + to-do API (from 1.6, copied into `app/`) into a **Docker container**, run it with a real Postgres database using one command, then put it **on the internet**.
**Like you're 10:** Docker is a lunchbox. You pack the food (code), the fork (Python) and the napkin (packages) together, so it works the same at school, at grandma's, or in the cloud.

## Part A: run it in Docker locally
1. Install Docker Desktop: https://www.docker.com/products/docker-desktop/
2. Build and start everything:
   ```bash
   cd level-1-apis/07-dockerize-and-deploy-to-the-cloud
   docker compose up --build
   ```
3. Open http://localhost:8000/docs. It's the same API, now inside a container and talking to Postgres.
4. Stop with `Ctrl+C`, then `docker compose down`. Add `-v` to also delete the database volume.

Useful commands:
```bash
docker ps                      # what's running
docker compose logs -f api     # watch the API's logs
docker compose exec db psql -U app -c "select * from users;"   # look inside Postgres
```

## Part B: deploy to Render (free tier)
1. Push this repo to your GitHub (already done if you cloned it from your account).
2. Go to https://render.com and sign up with GitHub.
3. Click **New + → Blueprint**, pick your repo, and set **Blueprint file path** to `ai-engineer-journey/level-1-apis/07-dockerize-and-deploy-to-the-cloud/render.yaml`.
   (Render may ask for the **root directory**. Use `ai-engineer-journey/level-1-apis/07-dockerize-and-deploy-to-the-cloud`.)
4. Click **Apply**. Render builds the Docker image, creates a Postgres database, and generates a random `SECRET_KEY`.
5. After a few minutes you get a URL like `https://login-todo-api.onrender.com`. Open `/docs` and sign up from your phone! 🎉

The free plan sleeps after inactivity, so the first request can take ~30 seconds.

**Railway alternative:** https://railway.app → New Project → Deploy from GitHub repo → set the root directory to this folder → add a PostgreSQL plugin → set the `DATABASE_URL` and `SECRET_KEY` variables.
Railway's Postgres URL starts with `postgresql://`. Change it to `postgresql+psycopg://` so SQLAlchemy uses psycopg 3.

## Key ideas
- **Image** = the recipe result (a frozen lunchbox). **Container** = a running copy of an image.
- **Layer caching:** we copy `requirements.txt` before the code, so editing code doesn't reinstall every package.
- **12-factor config:** the same image runs everywhere. Only environment variables (`DATABASE_URL`, `SECRET_KEY`, `PORT`) change.
- **Health check** (`/health`): the platform pings it to know your app is alive.

## Your turn
1. Add a `GET /version` route that returns an env var `APP_VERSION`, set it in `docker-compose.yml`, and rebuild.
2. Run the tests *inside* the container: `docker compose run --rm api pytest -q`.
3. Make the image smaller. Compare `docker images` before and after using `python:3.12-alpine` (does bcrypt still install?).

## Watch
- Docker in 100 seconds (Fireship): https://www.youtube.com/watch?v=Gjnup-PuquQ
- Docker tutorial for beginners (TechWorld with Nana): https://www.youtube.com/watch?v=3c-iBn73dDE
- FastAPI in containers: https://fastapi.tiangolo.com/deployment/docker/
