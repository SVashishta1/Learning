"""preflight.py: run this ON the customer's machine before go-live. It checks the boring things that break deployments.

    python preflight.py                                  # uses the same environment variables as the app
    PRIVATE_ONLY=1 EXPECT_NO_INTERNET=1 APP_URL=http://localhost:8000 python preflight.py

Exit code 0 = all checks passed (or skipped), 1 = at least one FAIL. Paste the output into the go-live ticket.
"""
import ipaddress
import os
import socket
import sys
from urllib.parse import urlparse

import httpx

from providers import read_secret

REQUIRED = {"anthropic": [], "bedrock": ["AWS_REGION"], "vertex": ["GCP_PROJECT", "GCP_REGION"],
            "ollama": ["OLLAMA_BASE_URL"], "fake": []}


def llm_host(provider: str) -> str | None:
    if provider == "anthropic":
        return "api.anthropic.com"
    if provider == "bedrock":
        return urlparse(os.getenv("BEDROCK_BASE_URL", "")).hostname or f"bedrock-mantle.{os.getenv('AWS_REGION', '')}.api.aws"
    if provider == "vertex":
        return f"{os.getenv('GCP_REGION', '')}-aiplatform.googleapis.com"
    if provider == "ollama":
        return urlparse(os.getenv("OLLAMA_BASE_URL", "")).hostname
    return None


def resolve(host: str) -> list[str]:
    return sorted({info[4][0] for info in socket.getaddrinfo(host, 443, proto=socket.IPPROTO_TCP)})


def can_connect(host: str, port: int, timeout: float = 3.0) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def run_checks() -> list[tuple[str, str, str]]:
    results = []                                     # (check, PASS/FAIL/SKIP, detail)
    provider = os.getenv("LLM_PROVIDER", "fake").lower()

    # 1. configuration
    if provider not in REQUIRED:
        results.append(("config: LLM_PROVIDER", "FAIL", f"unknown provider {provider!r}"))
        return results
    missing = [v for v in REQUIRED[provider] if not os.getenv(v)]
    results.append(("config: required variables", "FAIL" if missing else "PASS",
                    f"missing {missing}" if missing else f"provider={provider}"))

    # 2. secrets (never print them: only where they came from and how long they are)
    if provider == "anthropic":
        key = read_secret("ANTHROPIC_API_KEY")
        results.append(("secret: ANTHROPIC_API_KEY", "PASS" if key else "FAIL",
                        f"present ({len(key)} chars, starts {key[:7]}...)" if key else "not found in /run/secrets or env"))
    else:
        why = {"bedrock": "uses the machine's IAM role", "vertex": "uses the service account",
               "ollama": "local model, no key", "fake": "no key needed"}[provider]
        results.append(("secret: API key", "SKIP", f"{provider} {why}"))

    # 3. DNS for the model endpoint: inside a private network it should resolve to PRIVATE addresses
    host = llm_host(provider)
    if host:
        try:
            ips = resolve(host)
            private = all(ipaddress.ip_address(ip).is_private for ip in ips)
            if os.getenv("PRIVATE_ONLY") == "1" and not private:
                results.append(("dns: model endpoint is private", "FAIL", f"{host} -> {ips} (public: traffic would leave the VPC)"))
            else:
                results.append(("dns: model endpoint", "PASS", f"{host} -> {ips}{' (private)' if private else ''}"))
        except OSError as e:
            results.append(("dns: model endpoint", "FAIL", f"{host} does not resolve: {e}"))
    else:
        results.append(("dns: model endpoint", "SKIP", "fake provider"))

    # 4. egress: in a locked-down VPC, the open internet must NOT be reachable
    canary = os.getenv("CANARY_HOST", "1.1.1.1")
    reachable = can_connect(canary, 443)
    if os.getenv("EXPECT_NO_INTERNET") == "1":
        results.append(("egress: internet blocked", "FAIL" if reachable else "PASS",
                        f"{canary}:443 {'REACHABLE' if reachable else 'blocked'}"))
    else:
        results.append(("egress: internet", "SKIP", f"{canary}:443 {'reachable' if reachable else 'blocked'} (not enforced)"))

    # 5. the app itself
    url = os.getenv("APP_URL")
    if url:
        for path in ("/healthz", "/ready"):
            try:
                r = httpx.get(url.rstrip("/") + path, timeout=5)
                results.append((f"app: {path}", "PASS" if r.status_code == 200 else "FAIL", f"{r.status_code} {r.text[:80]}"))
            except httpx.HTTPError as e:
                results.append((f"app: {path}", "FAIL", f"{type(e).__name__}: {e}"))
    else:
        results.append(("app: health", "SKIP", "set APP_URL to check the running app"))
    return results


if __name__ == "__main__":
    rows = run_checks()
    for check, status, detail in rows:
        print(f"{ {'PASS': '✅', 'FAIL': '❌', 'SKIP': '➖'}[status]} {status:<4}  {check:<32} {detail}")
    failed = sum(s == "FAIL" for _, s, _ in rows)
    print(f"\n{len(rows)} checks, {failed} failed")
    sys.exit(1 if failed else 0)
