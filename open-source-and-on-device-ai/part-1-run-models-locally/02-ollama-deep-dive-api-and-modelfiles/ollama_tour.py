"""A guided tour of Ollama's REST API, using plain HTTP (httpx), so you see the real JSON.

Run:  python ollama_tour.py                      (uses llama3.2:3b)
      python ollama_tour.py --model kid-tutor    (your own model from the Modelfile)
"""
import argparse
import json
import math
import os
import sys

import httpx

OLLAMA = os.environ.get("OLLAMA_URL", "http://localhost:11434")  # where the Ollama server listens
EMBED_MODEL = "nomic-embed-text"                                  # a small model that turns text into numbers


def title(text):
    print(f"\n=== {text} ===")


def seconds(nanoseconds):
    """Ollama reports every duration in nanoseconds (billionths of a second)."""
    return nanoseconds / 1e9


def check_server(client):
    title("1. Is Ollama running?  GET /api/version")
    try:
        version = client.get("/api/version").json()["version"]
    except httpx.ConnectError:
        sys.exit(f"Can't reach Ollama at {OLLAMA}. Open the Ollama app (or run `ollama serve`) and try again.")
    print("Ollama version:", version)


def list_models(client, model):
    title("2. Which models are downloaded?  GET /api/tags")
    models = client.get("/api/tags").json()["models"]
    for m in models:
        print(f"  {m['name']:<28} {m['size'] / 1e9:5.2f} GB")
    names = [m["name"] for m in models]
    if model not in names:
        sys.exit(f"'{model}' is not downloaded. Run:  ollama pull {model}")
    return names


def generate(client, model):
    title("3. One question, one answer  POST /api/generate")
    body = {
        "model": model,
        "prompt": "In one sentence: why is the sky blue?",
        "stream": False,                                   # wait for the whole answer
        "options": {"temperature": 0, "num_ctx": 4096},   # 0 = always pick the most likely word
        "keep_alive": "10m",                               # keep the model in memory for 10 minutes
    }
    data = client.post("/api/generate", json=body).json()
    if "error" in data:
        sys.exit(f"Ollama says: {data['error']}")
    print(data["response"].strip())
    print(f"\n  loaded the model in  {seconds(data.get('load_duration', 0)):.2f} s")
    print(f"  read the prompt:     {data['prompt_eval_count']} tokens")
    speed = data["eval_count"] / seconds(data["eval_duration"])
    print(f"  wrote the answer:    {data['eval_count']} tokens at {speed:.1f} tokens/s")


def chat_streaming(client, model):
    title("4. A chat, streamed word by word  POST /api/chat")
    body = {
        "model": model,
        "messages": [
            {"role": "system", "content": "You answer in at most 3 short sentences."},
            {"role": "user", "content": "Give me two tips for learning to code."},
        ],
        "stream": True,  # send each piece of the answer as soon as it is ready
        "options": {"temperature": 0.7},
    }
    # The answer arrives as many small JSON objects, one per line ("NDJSON").
    with client.stream("POST", "/api/chat", json=body) as response:
        for line in response.iter_lines():
            if not line:
                continue
            chunk = json.loads(line)
            if "error" in chunk:
                sys.exit(f"Ollama says: {chunk['error']}")
            print(chunk["message"]["content"], end="", flush=True)
            if chunk["done"]:
                speed = chunk["eval_count"] / seconds(chunk["eval_duration"])
                print(f"\n\n  done_reason: {chunk['done_reason']} · {chunk['eval_count']} tokens at {speed:.1f} tokens/s")


def cosine(a, b):
    """How similar two vectors are: 1.0 = same direction, 0 = unrelated."""
    dot = sum(x * y for x, y in zip(a, b))
    return dot / (math.sqrt(sum(x * x for x in a)) * math.sqrt(sum(y * y for y in b)))


def embed(client, names):
    title(f"5. Text to numbers  POST /api/embed  ({EMBED_MODEL})")
    if not any(n.split(":")[0] == EMBED_MODEL for n in names):
        print(f"  Skipped: run  ollama pull {EMBED_MODEL}  to try this step.")
        return
    sentences = ["I love my dog.", "My puppy makes me happy.", "The train leaves at 9."]
    data = client.post("/api/embed", json={"model": EMBED_MODEL, "input": sentences}).json()
    vectors = data["embeddings"]  # one list of numbers per sentence
    print(f"  {len(vectors)} sentences -> {len(vectors)} vectors of {len(vectors[0])} numbers each")
    print(f"  first numbers of vector 1: {[round(x, 3) for x in vectors[0][:4]]} ...")
    print(f"  similarity dog/puppy: {cosine(vectors[0], vectors[1]):.2f}")
    print(f"  similarity dog/train: {cosine(vectors[0], vectors[2]):.2f}")


def running_models(client):
    title("6. What is in memory right now?  GET /api/ps")
    for m in client.get("/api/ps").json()["models"]:
        on_gpu = m["size_vram"] / m["size"] * 100 if m["size"] else 0
        print(f"  {m['name']:<28} {m['size'] / 1e9:5.2f} GB ({on_gpu:.0f}% on GPU), unloads at {m['expires_at'][:19]}")


def unload(client, model):
    title("7. Free the memory  POST /api/generate with keep_alive 0")
    client.post("/api/generate", json={"model": model, "keep_alive": 0})
    print(f"  {model} unloaded. The next request loads it again (a few seconds).")


def main():
    parser = argparse.ArgumentParser(description="Tour of the Ollama REST API.")
    parser.add_argument("--model", default="llama3.2:3b", help="model name, e.g. llama3.2:3b or kid-tutor")
    args = parser.parse_args()
    model = args.model if ":" in args.model else args.model + ":latest"  # Ollama adds ':latest' to bare names

    # One client for every request. timeout=300: the first request may wait while the model loads.
    with httpx.Client(base_url=OLLAMA, timeout=300) as client:
        check_server(client)
        names = list_models(client, model)
        generate(client, model)
        chat_streaming(client, model)
        embed(client, names)
        running_models(client)
        unload(client, model)


if __name__ == "__main__":
    main()
