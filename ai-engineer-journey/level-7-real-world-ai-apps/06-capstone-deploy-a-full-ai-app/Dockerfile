FROM python:3.12-slim
WORKDIR /srv
ENV PYTHONUNBUFFERED=1 EMBEDDER=tfidf PORT=8000
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app/ app/
COPY docs/ docs/
# Run as a non-root user: a basic container security habit
RUN useradd --create-home appuser && chown -R appuser /srv
USER appuser
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=3s CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT} --workers 2"]
