"""Measure how fast a model really runs on THIS device (a Raspberry Pi, a laptop...) through Ollama.

Run:  python speed_check.py                  (llama3.2:1b, 3 runs)
      python speed_check.py qwen2.5:0.5b --runs 5
Only needs httpx, so it's quick to install on a small device:  pip install httpx
"""
import argparse
import os
import platform
import statistics
import sys

import httpx

OLLAMA = os.environ.get("OLLAMA_URL", "http://localhost:11434")
PROMPT = "Explain in about 60 words why the sky is blue."

parser = argparse.ArgumentParser()
parser.add_argument("model", nargs="?", default="llama3.2:1b")
parser.add_argument("--runs", type=int, default=3)
args = parser.parse_args()

print(f"🖥️  {platform.node()} · {platform.machine()} · {platform.system()} · model {args.model}")
reading, writing = [], []
for run in range(1, args.runs + 1):
    try:
        data = httpx.post(f"{OLLAMA}/api/generate", timeout=600, json={
            "model": args.model, "prompt": PROMPT, "stream": False,
            "options": {"temperature": 0, "num_predict": 100, "num_ctx": 2048}}).json()
    except httpx.ConnectError:
        sys.exit(f"Can't reach Ollama at {OLLAMA}. Is it running? (sudo systemctl start ollama)")
    if "error" in data:
        sys.exit(f"Ollama says: {data['error']}. Try: ollama pull {args.model}")
    # Ollama measures in nanoseconds: tokens / (nanoseconds / 1e9) = tokens per second
    read_speed = data["prompt_eval_count"] / (data["prompt_eval_duration"] / 1e9)
    write_speed = data["eval_count"] / (data["eval_duration"] / 1e9)
    reading.append(read_speed)
    writing.append(write_speed)
    print(f"  run {run}: load {data['load_duration'] / 1e9:5.1f} s · reading the prompt {read_speed:6.1f} tok/s"
          f" · writing {write_speed:5.1f} tok/s")

print(f"\n📊 median: reading {statistics.median(reading):.1f} tok/s, writing {statistics.median(writing):.1f} tok/s")
print("   (5+ tok/s writing feels usable for chat; 10+ feels smooth; people read about 5-8 words per second)")
