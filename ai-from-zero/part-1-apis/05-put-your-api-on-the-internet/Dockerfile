# A recipe for a "container": a box with Python + your code inside, which runs the same anywhere.

# Start from a small Linux box that already has Python 3.12 installed.
FROM python:3.12-slim

# Work inside a folder called /app in the box.
WORKDIR /app

# Copy the list of add-ons first and install them (Docker caches this step, so rebuilds are faster).
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy your code into the box.
COPY main.py .

# The command the box runs when it starts. Hosts like Render tell us which port to use in $PORT;
# on your own computer $PORT is empty, so it falls back to 8000.
# "exec" makes uvicorn the main program in the box, so Ctrl + C can stop it.
CMD ["sh", "-c", "exec uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]
