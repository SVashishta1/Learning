# The clinic assistant app (the LLM runs in the separate "ollama" container).
FROM python:3.12-slim

# Don't write .pyc files; print logs straight away instead of buffering them.
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 HF_HUB_OFFLINE=1

WORKDIR /app

# Install the Python packages first: this layer is cached until requirements.txt changes.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Then copy the app itself (protocols/ and data/ are mounted at run time, see docker-compose.yml).
COPY clinic_rag.py ingest.py audit.py app.py check_offline.py ./
COPY static/ static/

# Run as a normal user, not root.
RUN useradd --create-home clinic && mkdir -p /app/data && chown clinic /app/data
USER clinic

EXPOSE 8000
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
