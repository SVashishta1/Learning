FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY assistant.py verify_no_egress.py ./
COPY knowledge ./knowledge
RUN useradd --create-home --uid 10001 assistant && mkdir -p /data && chown assistant /data
USER 10001
EXPOSE 8000
HEALTHCHECK --interval=15s --timeout=3s CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/healthz')"
CMD ["uvicorn", "assistant:app", "--host", "0.0.0.0", "--port", "8000"]
