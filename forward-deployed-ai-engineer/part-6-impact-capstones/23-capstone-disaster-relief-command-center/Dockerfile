# Small official Python image (Debian "slim" = fewer packages = smaller and safer)
FROM python:3.12-slim
# Don't write .pyc files; print logs immediately (no buffering), so `docker compose logs` is live
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
# Install dependencies first: this layer is cached until requirements.txt changes
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
# Never run as root inside the container
RUN useradd --create-home relief && chown -R relief /app
USER relief
EXPOSE 8000
HEALTHCHECK --interval=15s --timeout=3s CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/healthz')"
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
