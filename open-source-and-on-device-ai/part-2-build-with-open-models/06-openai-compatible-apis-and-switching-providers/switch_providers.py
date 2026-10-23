"""One piece of code, many AI providers: switch between local and cloud by changing base_url.

Run:  python switch_providers.py ollama "Why is the sky blue?"
      python switch_providers.py llamacpp "Why is the sky blue?" --stream
      python switch_providers.py all "Why is the sky blue?"        (ask every provider that is available)
      python switch_providers.py ollama --models                    (list the provider's models)
"""
import argparse
import os
import sys
import time

from openai import OpenAI, APIConnectionError, APIStatusError

# Settings for most providers. max_tokens is a safety limit on the answer length (and on cost).
COMMON_SETTINGS = {"temperature": 0.3, "max_tokens": 300}

# Every provider speaks the same "OpenAI-compatible" language. Only a few things change:
# where to send the request (base_url), the key, the model name, and sometimes a setting.
PROVIDERS = {
    "ollama": {
        "base_url": "http://localhost:11434/v1",
        "key_env": None,                         # local: no key needed
        "model": os.environ.get("OLLAMA_MODEL", "llama3.2:3b"),
        "settings": COMMON_SETTINGS,
    },
    "llamacpp": {
        "base_url": "http://localhost:8080/v1",  # llama-server --port 8080 (lesson 03)
        "key_env": None,
        "model": "local",                        # llama-server serves one model; the name is ignored
        "settings": COMMON_SETTINGS,
    },
    "vllm": {
        "base_url": "http://localhost:8000/v1",  # vllm serve ... (lesson 14)
        "key_env": None,
        "model": os.environ.get("VLLM_MODEL", "Qwen/Qwen2.5-1.5B-Instruct"),
        "settings": COMMON_SETTINGS,
    },
    "claude": {
        "base_url": "https://api.anthropic.com/v1/",  # Anthropic's OpenAI-compatible endpoint
        "key_env": "ANTHROPIC_API_KEY",
        "model": os.environ.get("CLAUDE_MODEL", "claude-haiku-5-5"),
        "settings": COMMON_SETTINGS,
    },
    "openai": {
        "base_url": "https://api.openai.com/v1",
        "key_env": "OPENAI_API_KEY",
        "model": os.environ.get("OPENAI_MODEL", "gpt-5-mini"),
        # OpenAI's newer models call the length limit max_completion_tokens and only allow the default temperature.
        "settings": {"max_completion_tokens": 300},
    },
}

SYSTEM = "You are a helpful assistant. Answer in at most 3 short sentences."


def make_client(name):
    """Build an OpenAI client that talks to the chosen provider."""
    p = PROVIDERS[name]
    key = os.environ.get(p["key_env"]) if p["key_env"] else "not-needed"  # local servers ignore the key
    if not key:
        raise RuntimeError(f"set {p['key_env']} first")
    return OpenAI(base_url=p["base_url"], api_key=key, timeout=300, max_retries=0)


def ask(name, question, stream=False):
    """Ask one question. Returns the answer text (and prints it as it arrives when stream=True)."""
    client = make_client(name)
    messages = [{"role": "system", "content": SYSTEM}, {"role": "user", "content": question}]
    model = PROVIDERS[name]["model"]
    settings = PROVIDERS[name]["settings"]  # ** below passes each setting as a named argument

    if not stream:
        response = client.chat.completions.create(model=model, messages=messages, **settings)
        return response.choices[0].message.content

    # stream=True: the answer arrives in small pieces ("chunks"); print each one immediately.
    pieces = []
    for chunk in client.chat.completions.create(model=model, messages=messages, stream=True, **settings):
        if chunk.choices and chunk.choices[0].delta.content:
            piece = chunk.choices[0].delta.content
            pieces.append(piece)
            print(piece, end="", flush=True)
    print()
    return "".join(pieces)


def list_models(name):
    for m in make_client(name).models.list():
        print(" ", m.id)


def main():
    parser = argparse.ArgumentParser(description="Ask the same question to different AI providers.")
    parser.add_argument("provider", choices=[*PROVIDERS, "all"])
    parser.add_argument("question", nargs="?", default="What is an open-weight model?")
    parser.add_argument("--stream", action="store_true", help="print the answer word by word")
    parser.add_argument("--models", action="store_true", help="list the provider's models and stop")
    args = parser.parse_args()

    names = list(PROVIDERS) if args.provider == "all" else [args.provider]
    for name in names:
        print(f"\n--- {name} ({PROVIDERS[name]['model']} at {PROVIDERS[name]['base_url']}) ---")
        start = time.perf_counter()
        try:
            if args.models:
                list_models(name)
                continue
            answer = ask(name, args.question, stream=args.stream)
            if not args.stream:
                print(answer.strip())
            print(f"({time.perf_counter() - start:.1f} s)")
        except APIConnectionError:
            print("skipped: nothing is listening there (is the server running?)")
        except APIStatusError as e:
            print(f"error {e.status_code}: {e.message}")
        except RuntimeError as e:
            print("skipped:", e)
            if args.provider != "all":
                sys.exit(1)


if __name__ == "__main__":
    main()
