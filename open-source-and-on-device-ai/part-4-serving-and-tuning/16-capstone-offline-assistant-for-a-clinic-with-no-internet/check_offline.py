"""The "no network" checklist, as a program. Run it on the clinic machine before going live.

Run:  python check_offline.py
It checks that the internet is NOT reachable, and that everything the assistant needs IS here.
"""
import os
import socket

import httpx

import audit
import clinic_rag

results = []


def check(passed, good, bad):
    results.append(passed)
    print(("✅ " if passed else "❌ ") + (good if passed else bad))


def internet_reachable(host, port=443):
    """Try to open a connection to a public server. On an air-gapped machine this must fail."""
    try:
        socket.create_connection((host, port), timeout=3).close()
        return True
    except OSError:
        return False


print("1. The internet must be OFF")
for host in ["1.1.1.1", "8.8.8.8", "huggingface.co", "ollama.com"]:
    check(not internet_reachable(host), f"cannot reach {host}", f"CAN reach {host}: this machine is online")

print("\n2. Software must not try to download anything")
check(os.environ.get("HF_HUB_OFFLINE") == "1", "HF_HUB_OFFLINE=1 (Hugging Face libraries stay offline)",
      "HF_HUB_OFFLINE is not 1 (set it, so voice models never try to download)")

print("\n3. Everything the assistant needs must be on this machine")
try:
    names = clinic_rag.installed_models()
    check(True, f"Ollama answers at {clinic_rag.OLLAMA_URL}", "")
    check(clinic_rag.has_model(clinic_rag.CHAT_MODEL, names), f"chat model {clinic_rag.CHAT_MODEL} is downloaded",
          f"chat model {clinic_rag.CHAT_MODEL} is missing (pull it BEFORE going offline)")
    check(clinic_rag.has_model(clinic_rag.EMBED_MODEL, names), f"embedding model {clinic_rag.EMBED_MODEL} is downloaded",
          f"embedding model {clinic_rag.EMBED_MODEL} is missing (pull it BEFORE going offline)")
except httpx.HTTPError:
    check(False, "", f"Ollama does not answer at {clinic_rag.OLLAMA_URL}")
check(clinic_rag.DB.exists(), f"search index exists ({clinic_rag.DB})", "no search index: run python ingest.py")
ok, message = audit.verify()
check(ok, f"audit log: {message}", f"audit log: {message}")

print(f"\n{'🟢 Ready for offline use' if all(results) else '🔴 Not ready: fix the ❌ lines above'} "
      f"({sum(results)}/{len(results)} checks passed)")
