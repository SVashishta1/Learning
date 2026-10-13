"""Talk to your running API from the terminal (streaming).  python chat_cli.py"""
import httpx

BASE = "http://127.0.0.1:8000"
cid = httpx.post(f"{BASE}/chats", json={}).json()["id"]
print(f"Conversation {cid}. Ctrl+C to quit.\n")
while True:
    text = input("you> ")
    print("bot> ", end="", flush=True)
    with httpx.stream("POST", f"{BASE}/chats/{cid}/stream", json={"content": text}, timeout=120) as r:
        for line in r.iter_lines():
            if line.startswith("data: ") and line != "data: [DONE]":
                print(line[6:], end="", flush=True)
    print("\n")
