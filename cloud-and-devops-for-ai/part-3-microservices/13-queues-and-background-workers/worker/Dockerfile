# worker image. Same recipe as lesson 08, but it runs a plain Python loop instead of a web server.

# ---------- Stage 1: install the packages ----------
FROM python:3.12-slim AS builder
RUN python -m venv --without-pip /opt/venv
COPY requirements.txt .
RUN pip --python /opt/venv/bin/python install --no-cache-dir -r requirements.txt

# ---------- Stage 2: the small image that actually runs ----------
FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH"
RUN useradd --create-home --uid 10001 app
WORKDIR /app
COPY --from=builder /opt/venv /opt/venv
COPY worker.py .
USER app

# No EXPOSE and no HEALTHCHECK: a worker has no web address. It only talks to Redis and the services.
CMD ["python", "worker.py"]
