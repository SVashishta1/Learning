# Part 2 · Docker

**A container is a lunch box for software.** Your app, the exact Python version, every package and setting go in one box that runs the same way on your laptop, your teammate's Mac and a cloud server. This is how almost every AI API is shipped today, and everything in Parts 3–5 (microservices, Kubernetes, the cloud) is built from containers.

**Time:** about 1–2 weeks at 1 hour a day · **Before this part:** [Part 1 · Git & GitHub](../part-1-git-and-github) (lesson 04's Mood API is the app we containerise)

| # | Lesson | What you'll have at the end |
|---|--------|-----------------------------|
| 05 | [What is a container?](05-what-is-a-container) | Docker installed, your first containers run, images vs containers clear in your head |
| 06 | [Running containers: ports, volumes, env](06-running-containers-ports-volumes-env) | a web server showing your own page, a database whose data survives, every `docker run` flag understood |
| 07 | [A Dockerfile for an AI API](07-dockerfile-for-an-ai-api) | your FastAPI Mood API in an image you built, with fast cached rebuilds |
| 08 | [Smaller, safer images](08-smaller-safer-images) | a 201 MB non-root image with a health check, instead of a 1.65 GB one |
| 09 | [Docker Compose: multi-container apps](09-docker-compose-multi-container-apps) | API + Postgres + Redis started with one command, in the right order |
| 10 | [Local LLMs in Docker](10-local-llms-in-docker) | an open LLM running in an Ollama container, called by your API container, with GPU notes |

## Install once for this part
Pick your system:

- **Windows 10/11:** install **WSL2 Ubuntu** first ([Linux from Zero, lesson 01](../../linux-from-zero/part-1-first-steps/01-what-is-linux-and-the-terminal)), then **Docker Desktop** from https://docs.docker.com/desktop/setup/install/windows-install/. In Docker Desktop → **Settings** → **Resources** → **WSL integration**, switch on your Ubuntu distro. Run every `docker` command in the Ubuntu terminal.
- **Mac:** install **Docker Desktop** from https://docs.docker.com/desktop/setup/install/mac-install/ (choose Apple silicon or Intel), open it once and wait for "Engine running".
- **Linux (Ubuntu/Debian):** install **Docker Engine** with the official steps at https://docs.docker.com/engine/install/ubuntu/, then let your user run Docker without `sudo` and log out and in again:
  ```bash
  sudo usermod -aG docker $USER
  ```
  (`usermod` = modify a user; `-aG docker` = **a**ppend them to the **G**roup `docker`; `$USER` = your user name.)

Check it works:
```bash
docker version
docker compose version
docker run hello-world
```
You should see a `Client` and a `Server` section, a Compose version (v2 or newer), and "Hello from Docker!".

**Disk space:** lessons 05–09 need about 3 GB. Lesson 10 needs about 10 GB more (the Ollama image is about 3.4 GB to download and about 8.4 GB once unpacked, plus the model). `docker system df` shows what Docker uses; each lesson ends with clean-up commands.

**Python packages:** none for the containers themselves (they install their own). If you want to run an app outside Docker too, each lesson folder has a `requirements.txt`: `pip install -r requirements.txt` in a venv.

## After this part you'll be able to
- Explain images, containers, layers, registries, volumes, bind mounts and networks in plain words.
- Run any service with the right `docker run` flags (`-d -p -v -e --name --rm -it`) and debug it with `logs`, `exec`, `ps`, `stop` and `rm`.
- Write a Dockerfile for a Python AI API that rebuilds in under a second when only code changes.
- Shrink and harden images: slim bases, multi-stage builds, a non-root user, `.dockerignore` and a `HEALTHCHECK`.
- Describe a multi-container app in `compose.yaml`, with start-up order, health checks, private networks and persistent volumes.
- Run an open LLM in a container, keep its models in a volume, call it from another container, and know how to give it an NVIDIA GPU.

**Every lesson works the same way:** `cd` into its folder from the course folder (`cloud-and-devops-for-ai`), follow **Run it** step by step, compare with **What you should see**, then read **How it works**.

## Next
Start with → [05 · What is a container?](05-what-is-a-container). When you finish lesson 10, go on to → [Part 3 · Microservices](../part-3-microservices).
