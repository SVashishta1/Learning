# A Dockerfile is a recipe for a box (image) that contains Python + your code + its packages.
FROM python:3.12-slim

WORKDIR /code

# Copy requirements first: Docker caches this layer, so rebuilds are fast when only code changes
COPY app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ .

# Cloud platforms tell you which port to use through $PORT (default 8000 locally)
ENV PORT=8000
EXPOSE 8000
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT}"]
