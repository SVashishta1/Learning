"""Ask a question to a running llama-server and show how fast it answered.

Start the server first (see the README), then run:
      python ask_llama_server.py "What is a GGUF file?"
"""
import os
import sys

import httpx

SERVER = os.environ.get("LLAMA_SERVER_URL", "http://localhost:8080")
question = " ".join(sys.argv[1:]) or "In two sentences, what is llama.cpp?"

try:
    health = httpx.get(f"{SERVER}/health", timeout=5)  # 200 = ready, 503 = still loading the model
except httpx.ConnectError:
    sys.exit(f"Can't reach llama-server at {SERVER}. Start it with: llama-server -m <model.gguf> --port 8080")
if health.status_code != 200:
    sys.exit(f"The server is not ready yet ({health.status_code}): {health.text}. Wait a few seconds.")

body = {
    # llama-server serves one model, so any name works here; it is kept for OpenAI compatibility.
    "model": "local",
    "messages": [
        {"role": "system", "content": "You are a helpful assistant. Answer briefly."},
        {"role": "user", "content": question},
    ],
    "temperature": 0.2,
    "max_tokens": 200,  # stop after 200 tokens at most
}
reply = httpx.post(f"{SERVER}/v1/chat/completions", json=body, timeout=300).json()

print("Q:", question)
print("A:", reply["choices"][0]["message"]["content"].strip())

# llama-server adds a "timings" section that OpenAI's API does not have.
t = reply.get("timings", {})
usage = reply["usage"]
print(f"\nprompt:  {usage['prompt_tokens']} tokens read at {t.get('prompt_per_second', 0):.1f} tokens/s")
print(f"answer:  {usage['completion_tokens']} tokens written at {t.get('predicted_per_second', 0):.1f} tokens/s")
print(f"finish:  {reply['choices'][0]['finish_reason']}  (stop = it finished, length = hit max_tokens)")
