# The fixed version of ../insecure/Dockerfile.

# GOOD: a small, pinned base image (fewer packages = fewer holes). For even stricter
# builds, pin the exact digest too: FROM python:3.12-slim@sha256:<digest>
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# GOOD: a normal user with a fixed id (Kubernetes runAsNonRoot can check it)
RUN useradd --create-home --uid 10001 app
WORKDIR /app

# GOOD: COPY only what is needed, dependencies first (cached layer)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY main.py .

# GOOD: no secrets in the image. They arrive at run time as a file or env variable.
USER 10001
EXPOSE 8000

# GOOD: Docker can tell when the app is unhealthy
HEALTHCHECK --interval=30s --timeout=3s --retries=3 \
    CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=2)"]

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
