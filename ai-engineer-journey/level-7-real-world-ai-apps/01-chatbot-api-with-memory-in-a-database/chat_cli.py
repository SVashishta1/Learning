"""Talk to your running API from the terminal (streaming).  python chat_cli.py"""
import json
import sys

import httpx

BASE = "http://127.0.0.1:8000"
try:
    cid = httpx.post(f"{BASE}/chats", json={}).json()["id"]
except httpx.ConnectError:
    sys.exit("Can't reach the API. Start it first in another terminal: uvicorn main:app --reload")
print(f"Conversation {cid}. Type 'quit' (or press Ctrl+C) to leave.\n")
while True:
    try:
        text = input("you> ").strip()
    except (EOFError, KeyboardInterrupt):
        break
    if text.lower() in {"quit", "exit"}:
        break
    if not text:
        continue
    print("bot> ", end="", flush=True)
    with httpx.stream("POST", f"{BASE}/chats/{cid}/stream", json={"content": text}, timeout=120) as r:
        for line in r.iter_lines():              # Server-Sent Events: lines starting with "data: "
            if line.startswith("data: ") and line != "data: [DONE]":
                print(json.loads(line[6:]), end="", flush=True)   # each piece is a JSON string
    print("\n")
