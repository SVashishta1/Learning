# A Dockerfile is a recipe. Docker reads it from top to bottom and
# turns each instruction into one layer of the finished image.

# 1. Start from an image that already has Python 3.12 on a small Debian Linux.
FROM python:3.12-slim

# 2. Print Python output straight away (no buffering), so `docker logs` shows it live.
ENV PYTHONUNBUFFERED=1

# 3. Work inside the folder /app in the image (Docker creates it).
WORKDIR /app

# 4. Copy ONLY the shopping list first, then install it.
#    These two layers are reused from the cache until requirements.txt changes.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copy the code last: it changes most often, so only this cheap layer is rebuilt.
COPY main.py .

# 6. Note for humans and tools: the app listens on port 8000.
EXPOSE 8000

# 7. The command that runs when a container starts.
#    --host 0.0.0.0 = accept visitors from outside the container, not just from inside it.
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
