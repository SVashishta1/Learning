# The "production" Dockerfile: small, fast to rebuild, runs as a normal user,
# and tells Docker how to check that the app is healthy.

# ---------- Stage 1: "builder" = the messy workshop ----------
FROM python:3.12-slim AS builder

# Put every package in its own folder (a virtual environment), so stage 2 can copy it in one go.
# --without-pip: the installer (pip) stays here in the workshop; only the packages travel on.
RUN python -m venv --without-pip /opt/venv

COPY requirements.txt .
# --python /opt/venv/bin/python = "use the system pip, but install INTO the venv".
RUN pip --python /opt/venv/bin/python install --no-cache-dir -r requirements.txt


# ---------- Stage 2: "runtime" = the clean shop window ----------
# A brand-new slim image. Nothing from stage 1 comes along unless we COPY it.
FROM python:3.12-slim

# No .pyc files, no output buffering, and use the venv's python/uvicorn first.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH"

# Create a normal (non-root) user called "app" with user id 10001.
RUN useradd --create-home --uid 10001 app

WORKDIR /app

# Take ONLY the finished packages from the builder stage.
COPY --from=builder /opt/venv /opt/venv
COPY main.py .

# From here on, everything (including the running app) is done as "app", not root.
USER app

EXPOSE 8000

# Every 30 s, Docker runs this command inside the container. Exit code 0 = healthy.
# The slim image has no curl, so we use Python's built-in urllib.
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
    CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=2)"]

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
