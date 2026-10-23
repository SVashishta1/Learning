"""A mini benchmark for Ollama models: load time, time to first token, speed and memory.

Run:  python benchmark.py llama3.2:1b llama3.2:3b qwen2.5:3b
      python benchmark.py llama3.2:3b --runs 5
Results are printed as a table and saved to results.csv.
"""
import argparse
import csv
import json
import os
import statistics
import sys
import time

import httpx

OLLAMA = os.environ.get("OLLAMA_URL", "http://localhost:11434")
PROMPTS = [
    "Explain in about 80 words why the sea is salty.",
    "Write a short, friendly email inviting a colleague to lunch on Friday.",
    "List five tips for keeping a houseplant alive, one line each.",
]
OPTIONS = {"temperature": 0, "seed": 42, "num_predict": 128, "num_ctx": 4096}  # the same settings for every model


def stream_once(client, model, prompt):
    """Send one prompt with streaming on, and time it with a stopwatch.

    Returns (time to first token in seconds, the final chunk with Ollama's own statistics)."""
    body = {"model": model, "prompt": prompt, "stream": True, "options": OPTIONS}
    start = time.perf_counter()
    first_token = None
    with client.stream("POST", "/api/generate", json=body) as response:
        for line in response.iter_lines():
            if not line:
                continue
            chunk = json.loads(line)
            if "error" in chunk:
                sys.exit(f"Ollama says: {chunk['error']}  (try: ollama pull {model})")
            if first_token is None and chunk.get("response"):
                first_token = time.perf_counter() - start  # the first piece of text has arrived
            if chunk["done"]:
                return first_token or 0.0, chunk


def memory_of(client, model):
    """Ask Ollama how much memory the loaded model uses, and how much of it is on the GPU."""
    for m in client.get("/api/ps").json()["models"]:
        if m["name"] == model:
            return m["size"] / 1e9, (m["size_vram"] / m["size"] * 100 if m["size"] else 0)
    return 0.0, 0.0


def benchmark(client, model, runs):
    print(f"\n{model}")
    # Warm-up: the first request loads the model from disk into memory. We time it separately.
    client.post("/api/generate", json={"model": model, "keep_alive": 0})  # make sure it starts unloaded
    _, warm = stream_once(client, model, "Say hello.")
    load_s = warm.get("load_duration", 0) / 1e9
    print(f"  loaded in {load_s:.1f} s")

    ttfts, gen_speeds, prompt_speeds = [], [], []
    for i in range(runs):
        prompt = PROMPTS[i % len(PROMPTS)]
        ttft, stats = stream_once(client, model, prompt)
        gen = stats["eval_count"] / (stats["eval_duration"] / 1e9)                # tokens written per second
        read = stats["prompt_eval_count"] / max(stats["prompt_eval_duration"] / 1e9, 1e-9)  # tokens read per second
        ttfts.append(ttft)
        gen_speeds.append(gen)
        prompt_speeds.append(read)
        print(f"  run {i + 1}: first token after {ttft * 1000:.0f} ms, {stats['eval_count']} tokens at {gen:.1f} tokens/s")

    size_gb, gpu_pct = memory_of(client, model)
    client.post("/api/generate", json={"model": model, "keep_alive": 0})  # unload, so the next model has room
    return {
        "model": model,
        "load_s": round(load_s, 2),
        "ttft_ms": round(statistics.median(ttfts) * 1000),          # median = the middle value, ignores one odd run
        "gen_tok_s": round(statistics.median(gen_speeds), 1),
        "prompt_tok_s": round(statistics.median(prompt_speeds), 1),
        "memory_gb": round(size_gb, 2),
        "gpu_pct": round(gpu_pct),
    }


def main():
    parser = argparse.ArgumentParser(description="Benchmark Ollama models.")
    parser.add_argument("models", nargs="+", help="model names, e.g. llama3.2:1b llama3.2:3b")
    parser.add_argument("--runs", type=int, default=3, help="measured runs per model (default 3)")
    args = parser.parse_args()

    with httpx.Client(base_url=OLLAMA, timeout=600) as client:
        try:
            client.get("/api/version")
        except httpx.ConnectError:
            sys.exit(f"Can't reach Ollama at {OLLAMA}. Open the Ollama app or run `ollama serve`.")
        # Ollama calls "llama3.2" "llama3.2:latest", so add the tag if it is missing.
        models = [m if ":" in m else m + ":latest" for m in args.models]
        rows = [benchmark(client, model, args.runs) for model in models]

    print(f"\n{'model':<22}{'load s':>8}{'TTFT ms':>9}{'gen tok/s':>11}{'read tok/s':>12}{'memory':>9}{'GPU':>6}")
    for r in rows:
        print(f"{r['model']:<22}{r['load_s']:>8}{r['ttft_ms']:>9}{r['gen_tok_s']:>11}"
              f"{r['prompt_tok_s']:>12}{r['memory_gb']:>7.2f}GB{r['gpu_pct']:>5}%")

    with open("results.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    print("\nSaved results.csv (open it in a spreadsheet to compare runs over time).")


if __name__ == "__main__":
    main()
