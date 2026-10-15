"""Project 6.5 part A: chat with an open LLM running LOCALLY through Ollama's HTTP API.

1. Install Ollama: https://ollama.com/download
2. ollama pull llama3.2:3b       (or qwen2.5:3b, gemma3:4b ... ~2 GB)
3. python ollama_chat.py
"""
import json
import sys

import httpx

MODEL = sys.argv[1] if len(sys.argv) > 1 else "llama3.2:3b"
URL = "http://localhost:11434/api/chat"
history = [{"role": "system", "content": "You are a friendly tutor. Keep answers under 80 words."}]

print(f"Chatting with {MODEL} running on YOUR machine. Type 'quit' to exit.\n")
while True:
    try:
        user = input("you> ").strip()
    except (EOFError, KeyboardInterrupt):        # Ctrl+D / Ctrl+C also exit cleanly
        break
    if user.lower() in {"quit", "exit"}:
        break
    if not user:
        continue
    history.append({"role": "user", "content": user})
    reply = ""
    try:
        # stream=True: tokens arrive one by one, just like ChatGPT's typing effect
        with httpx.stream("POST", URL, json={"model": MODEL, "messages": history, "stream": True}, timeout=120) as r:
            if r.status_code != 200:                # e.g. 404 when the model hasn't been pulled yet
                r.read()
                sys.exit(f"Ollama error {r.status_code}: {r.text}\nTry: ollama pull {MODEL}")
            print("bot> ", end="", flush=True)
            for line in r.iter_lines():
                if line:
                    piece = json.loads(line).get("message", {}).get("content", "")
                    reply += piece
                    print(piece, end="", flush=True)
        print("\n")
    except httpx.ConnectError:
        sys.exit("Ollama isn't running. Install it from https://ollama.com and run: ollama pull " + MODEL)
    history.append({"role": "assistant", "content": reply})   # remember the conversation
