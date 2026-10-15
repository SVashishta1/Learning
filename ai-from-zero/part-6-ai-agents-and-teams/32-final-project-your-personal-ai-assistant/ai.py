# ai.py: a tiny helper that talks to Claude for you. Every project in Parts 4-6 uses this same file.
# You don't need to understand all of it. Just know: ask(...) sends messages to Claude and returns its reply.
import os

import anthropic

MODEL = os.getenv("CLAUDE_MODEL", "claude-opus-5-5")   # set CLAUDE_MODEL=claude-haiku-5-5 for the cheapest option
KEY_HELP = "See 'Get your API key' in the Part 4 README (part-4-chatbots/README.md)."
_client = None


def client():
    global _client
    if _client is None:
        if not os.getenv("ANTHROPIC_API_KEY"):          # the most common beginner problem, so check it first
            raise SystemExit("❌ ANTHROPIC_API_KEY is not set in this terminal. " + KEY_HELP)
        _client = anthropic.Anthropic()                 # reads your ANTHROPIC_API_KEY
    return _client


def _safety_net():
    # On these models: if a request is ever declined, Claude automatically retries it on another model.
    if MODEL in {"claude-opus-5-5", "claude-opus-5", "claude-fable-5-1", "claude-sonnet-5-5"}:
        return {"betas": ["server-side-fallback-2026-07-01"], "fallbacks": "default"}
    return {}


def send(**request):
    """Send a raw request to Claude and get the full response back (used for tools and agents)."""
    try:
        return client().beta.messages.create(model=MODEL, **_safety_net(), **request)
    except anthropic.AuthenticationError:
        raise SystemExit("❌ Your API key is wrong or was deleted. " + KEY_HELP)


def ask(messages, system="You are a helpful assistant.", max_tokens=2000):
    """messages: a list like [{"role": "user", "content": "Hi!"}]. Returns Claude's reply as text."""
    if isinstance(messages, str):
        messages = [{"role": "user", "content": messages}]
    response = send(messages=messages, system=system, max_tokens=max_tokens)
    return "".join(block.text for block in response.content if block.type == "text")


def stream(messages, system="You are a helpful assistant.", max_tokens=2000):
    """Like ask(), but yields the reply piece by piece as it's being written."""
    try:
        with client().beta.messages.stream(model=MODEL, **_safety_net(), messages=messages,
                                           system=system, max_tokens=max_tokens) as live:
            yield from live.text_stream
    except anthropic.AuthenticationError:
        raise SystemExit("❌ Your API key is wrong or was deleted. " + KEY_HELP)


def ask_for_data(prompt, shape, system="Extract the information exactly as written. Use null if missing."):
    """Ask Claude to fill in a Pydantic 'shape' (a form). Returns a filled-in Python object, not text."""
    try:
        response = client().beta.messages.parse(model=MODEL, **_safety_net(), max_tokens=4000, system=system,
                                                output_format=shape, messages=[{"role": "user", "content": prompt}])
    except anthropic.AuthenticationError:
        raise SystemExit("❌ Your API key is wrong or was deleted. " + KEY_HELP)
    return response.parsed_output
