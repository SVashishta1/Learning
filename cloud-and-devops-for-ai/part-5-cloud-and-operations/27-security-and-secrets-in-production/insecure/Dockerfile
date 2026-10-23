# DELIBERATELY INSECURE. Every "BAD" line is a mistake that trivy should find.
# Compare it with ../secure/Dockerfile. Never copy this file.

# BAD: "latest" changes without warning, and the full image is huge (more software = more holes)
FROM python:latest

# BAD: a secret in ENV is stored inside the image; anyone who can pull the image can read it
ENV ANTHROPIC_API_KEY=put-your-real-key-here

# BAD: ADD can download from the internet and unpack archives by surprise; prefer COPY
ADD . /app
WORKDIR /app

RUN pip install -r requirements.txt

# BAD: no USER line, so the app runs as root inside the container
EXPOSE 8000
CMD ["python", "-m", "http.server", "8000"]
