"""A tiny API used to show a hardened image. It reads its secret from a file or env, never logs it."""

import os
from pathlib import Path

from fastapi import FastAPI

app = FastAPI(title="Secure API")


def has_api_key() -> bool:
    # Prefer a mounted secret file (Kubernetes / Docker secrets), fall back to an environment variable.
    secret_file = Path("/run/secrets/anthropic_api_key")
    return secret_file.is_file() or bool(os.getenv("ANTHROPIC_API_KEY"))


@app.get("/health")
def health():
    return {"status": "ok", "api_key_configured": has_api_key()}
