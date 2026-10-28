"""verify_no_egress.py: prove that this machine/container cannot reach the internet, but CAN reach the model server.

    docker compose exec assistant python verify_no_egress.py
Exit code 0 = isolated as expected. Attach the output to the security sign-off.
"""
import os
import socket
import sys

import httpx

PUBLIC_TARGETS = [("1.1.1.1", 443), ("8.8.8.8", 53), ("pypi.org", 443), ("huggingface.co", 443), ("ollama.com", 443)]


def reachable(host: str, port: int) -> str:
    try:
        with socket.create_connection((host, port), timeout=3):
            return "REACHABLE"
    except socket.gaierror:
        return "no DNS"
    except OSError as e:
        return f"blocked ({e.__class__.__name__})"


def main() -> int:
    bad = 0
    for host, port in PUBLIC_TARGETS:
        result = reachable(host, port)
        ok = result != "REACHABLE"
        bad += not ok
        print(f"{'✅' if ok else '❌'} internet {host}:{port:<5} {result}")
    if os.getenv("FAKE_LLM") != "1":
        url = os.getenv("MODEL_URL", "http://ollama:11434/v1").rstrip("/") + "/models"
        try:
            httpx.get(url, timeout=5, trust_env=False).raise_for_status()
            print(f"✅ internal  {url} reachable")
        except httpx.HTTPError as e:
            bad += 1
            print(f"❌ internal  {url} NOT reachable: {type(e).__name__}")
    print("\nISOLATED: no internet access" if not bad else f"\nNOT ISOLATED: {bad} problem(s)")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
