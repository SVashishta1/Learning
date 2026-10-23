# llm-service image. Same recipe as lesson 08, plus a VERSION you can choose at build time.

# ---------- Stage 1: install the packages ----------
FROM python:3.12-slim AS builder
RUN python -m venv --without-pip /opt/venv
COPY requirements.txt .
RUN pip --python /opt/venv/bin/python install --no-cache-dir -r requirements.txt

# ---------- Stage 2: the small image that actually runs ----------
FROM python:3.12-slim
# ARG = a value you can pass to "docker build --build-arg VERSION=2.0". Default 1.0.
ARG VERSION=1.0
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH" \
    SERVICE_VERSION=$VERSION
RUN useradd --create-home --uid 10001 app
WORKDIR /app
COPY --from=builder /opt/venv /opt/venv
COPY main.py .
USER app
EXPOSE 8000

HEALTHCHECK --interval=10s --timeout=3s --start-period=10s --start-interval=1s --retries=3 \
    CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=2)"]

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
