"""Ask a vLLM server one question, with the OpenAI SDK, and watch the answer stream in.

Run:  python ask_vllm.py "Why is the sky blue?"
      LLM_URL=http://localhost:11434/v1 LLM_MODEL=llama3.2:3b python ask_vllm.py "Hi"   (same code, Ollama)
"""
import os
import sys
import time

from openai import APIConnectionError, OpenAI

URL = os.environ.get("LLM_URL", "http://localhost:8000/v1")            # vllm serve listens on port 8000
MODEL = os.environ.get("LLM_MODEL", "Qwen/Qwen2.5-1.5B-Instruct")      # must match the served model name
KEY = os.environ.get("LLM_API_KEY", "not-needed")                       # only checked if you started vLLM with --api-key

client = OpenAI(base_url=URL, api_key=KEY)
question = " ".join(sys.argv[1:]) or "In two sentences, what is vLLM?"

start = time.perf_counter()
first = None
try:
    stream = client.chat.completions.create(
        model=MODEL, stream=True, max_tokens=200, temperature=0.7,
        messages=[{"role": "system", "content": "You are a helpful assistant. Be brief."},
                  {"role": "user", "content": question}])
    for chunk in stream:
        piece = chunk.choices[0].delta.content if chunk.choices else None
        if piece:
            if first is None:
                first = time.perf_counter() - start                    # time to first token
            print(piece, end="", flush=True)
except APIConnectionError:
    sys.exit(f"Can't reach {URL}. Is the server running? (vllm serve {MODEL})")
total = time.perf_counter() - start
print(f"\n\n⏱  first token after {first or 0:.2f} s, whole answer in {total:.2f} s ({MODEL} at {URL})")
