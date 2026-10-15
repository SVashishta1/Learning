# A Dockerfile is a recipe for a box (image) that contains Python + your code + its packages.
FROM python:3.12-slim

# Don't write .pyc files, and print logs straight away (so `docker compose logs` shows them live)
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1

WORKDIR /code

# Copy requirements first: Docker caches this layer, so rebuilds are fast when only code changes
COPY app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ .

# Cloud platforms tell you which port to use through $PORT (Render uses 10000, Railway picks one).
# Locally it defaults to 8000. `exec` lets uvicorn receive Ctrl+C / stop signals directly.
ENV PORT=8000
EXPOSE 8000
CMD ["sh", "-c", "exec uvicorn main:app --host 0.0.0.0 --port ${PORT}"]
