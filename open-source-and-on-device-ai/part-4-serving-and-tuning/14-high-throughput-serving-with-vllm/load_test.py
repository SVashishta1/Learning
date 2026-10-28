"""Pretend to be many users at once, and measure how an OpenAI-compatible server copes.

Run:  python load_test.py vllm   --users 16 --requests 64
      python load_test.py ollama --users 16 --requests 64
      python load_test.py --url http://localhost:8080/v1 --model local   (any other server, e.g. llama-server)
Prints: requests per second, output tokens per second (all users together),
        time to first token and total time per request (median and 95th percentile).
"""
import argparse
import asyncio
import os
import statistics
import time

from openai import APIConnectionError, AsyncOpenAI

TARGETS = {
    "vllm": ("http://localhost:8000/v1", os.environ.get("VLLM_MODEL", "Qwen/Qwen2.5-1.5B-Instruct")),
    "ollama": ("http://localhost:11434/v1", os.environ.get("OLLAMA_MODEL", "qwen2.5:1.5b")),
}
QUESTIONS = [
    "Write a short story about a lighthouse keeper.",
    "Explain how a bicycle stays upright.",
    "Give me five ideas for a rainy Sunday.",
    "Describe how bread rises, for a child.",
]


async def one_request(client, model, question, max_tokens):
    """Send one streaming request. Returns (seconds to first token, total seconds, output tokens)."""
    start = time.perf_counter()
    first, pieces, usage_tokens = None, 0, None
    stream = await client.chat.completions.create(
        model=model, messages=[{"role": "user", "content": question}], max_tokens=max_tokens,
        temperature=0.7, stream=True, stream_options={"include_usage": True})   # last chunk carries token counts
    async for chunk in stream:
        if chunk.usage:
            usage_tokens = chunk.usage.completion_tokens
        if chunk.choices and chunk.choices[0].delta.content:
            if first is None:
                first = time.perf_counter() - start
            pieces += 1
    total = time.perf_counter() - start
    return first if first is not None else total, total, usage_tokens or pieces


async def user(client, model, jobs, max_tokens, results):
    """One pretend user: takes the next job from the shared list until none are left."""
    while jobs:
        question = jobs.pop()
        results.append(await one_request(client, model, question, max_tokens))


def p95(values):
    return sorted(values)[max(0, round(0.95 * len(values)) - 1)]


async def main():
    parser = argparse.ArgumentParser(description="Load-test an OpenAI-compatible LLM server.")
    parser.add_argument("target", nargs="?", choices=TARGETS, default="vllm")
    parser.add_argument("--url", help="base URL, e.g. http://localhost:8000/v1 (overrides the target)")
    parser.add_argument("--model", help="model name (overrides the target)")
    parser.add_argument("--users", type=int, default=8, help="how many users send requests at the same time")
    parser.add_argument("--requests", type=int, default=32, help="how many requests in total")
    parser.add_argument("--max-tokens", type=int, default=128, help="length limit of each answer")
    args = parser.parse_args()
    url = args.url or TARGETS[args.target][0]
    model = args.model or TARGETS[args.target][1]

    client = AsyncOpenAI(base_url=url, api_key=os.environ.get("LLM_API_KEY", "not-needed"), timeout=600)
    jobs = [QUESTIONS[i % len(QUESTIONS)] for i in range(args.requests)]
    results = []
    print(f"🚦 {args.requests} requests, {args.users} users at a time, up to {args.max_tokens} tokens each → {model} at {url}")
    await one_request(client, model, "Say hi.", 8)                  # warm-up: load the model before timing
    start = time.perf_counter()
    await asyncio.gather(*(user(client, model, jobs, args.max_tokens, results) for _ in range(args.users)))
    wall = time.perf_counter() - start

    ttft = [r[0] for r in results]
    latency = [r[1] for r in results]
    tokens = sum(r[2] for r in results)
    print(f"\n  finished in            {wall:7.1f} s")
    print(f"  requests per second    {len(results) / wall:7.2f}")
    print(f"  output tokens/s (all)  {tokens / wall:7.1f}")
    print(f"  first token  median    {statistics.median(ttft):7.2f} s    p95 {p95(ttft):6.2f} s")
    print(f"  whole answer median    {statistics.median(latency):7.2f} s    p95 {p95(latency):6.2f} s")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except APIConnectionError:
        raise SystemExit("Can't reach the server. Start it first (see the README), or check --url.")
