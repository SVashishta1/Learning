# llm.py: one small helper that talks to an AI model for you. Every lesson in this course that uses an LLM
# has the same copy of this file, so you only need to read it once.
#
#   ask("question")              -> the model's answer as text
#   ask_json("question", Shape)  -> the answer as a filled-in Pydantic object (a typed form)
#
# Which model? Two choices, picked with environment variables (settings in your terminal):
#   Claude (default):  export ANTHROPIC_API_KEY=sk-ant-...     optional: export CLAUDE_MODEL=claude-haiku-5-5
#   Local Ollama:      export LLM_PROVIDER=ollama              optional: export OLLAMA_MODEL=llama3.2
import json
import os

PROVIDER = os.getenv("LLM_PROVIDER", "anthropic").lower()           # "anthropic" or "ollama"
CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-opus-5-5")         # claude-haiku-5-5 is the cheap, fast option
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")                # any model you pulled with `ollama pull`
OLLAMA_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")   # Ollama's OpenAI-compatible address

# On these Claude models we switch on "server-side fallback": if a request is ever declined,
# Anthropic's servers retry it on another model inside the same call.
_FALLBACK_MODELS = {"claude-opus-5-5", "claude-opus-5", "claude-fable-5-1", "claude-sonnet-5-5"}
_client = None   # created on first use, then reused (tests swap in a fake here)


def get_client():
    """Create the connection to the model once, with a clear message if something is missing."""
    global _client
    if _client is None:
        if PROVIDER == "ollama":
            from openai import OpenAI                                   # Ollama speaks the OpenAI API format
            _client = OpenAI(base_url=OLLAMA_URL, api_key="ollama")     # the key is required by the library but ignored
        else:
            if not os.getenv("ANTHROPIC_API_KEY"):                     # the most common problem, so check it first
                raise SystemExit("ANTHROPIC_API_KEY is not set in this terminal. "
                                 "Set it (see the course README), or use a local model: export LLM_PROVIDER=ollama")
            import anthropic
            _client = anthropic.Anthropic()                             # reads ANTHROPIC_API_KEY by itself
    return _client


def model_name():
    return OLLAMA_MODEL if PROVIDER == "ollama" else CLAUDE_MODEL


def _claude_extras():
    if CLAUDE_MODEL in _FALLBACK_MODELS:
        return {"betas": ["server-side-fallback-2026-07-01"], "fallbacks": "default"}
    return {}


def ask(prompt, system="You are a helpful assistant.", max_tokens=2000):
    """Send one question, get the answer back as plain text."""
    client = get_client()
    if PROVIDER == "ollama":
        reply = client.chat.completions.create(
            model=OLLAMA_MODEL, max_tokens=max_tokens,
            messages=[{"role": "system", "content": system}, {"role": "user", "content": prompt}])
        return reply.choices[0].message.content or ""
    reply = client.beta.messages.create(model=CLAUDE_MODEL, max_tokens=max_tokens, system=system,
                                        messages=[{"role": "user", "content": prompt}], **_claude_extras())
    if reply.stop_reason == "refusal":
        raise RuntimeError("The model declined this request.")
    return "".join(block.text for block in reply.content if block.type == "text")


def _json_part(text):
    """Small local models sometimes wrap JSON in ```fences``` or chatter. Keep only the {...} part."""
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end == -1:
        raise ValueError(f"The model did not return JSON. It said: {text[:200]!r}")
    return text[start:end + 1]


def ask_json(prompt, shape, system="Fill in the form using only the information given. Use null when unknown.",
             max_tokens=4000):
    """Ask the model to fill in a Pydantic 'shape'. Returns a checked Python object, not text."""
    client = get_client()
    if PROVIDER == "ollama":
        schema = shape.model_json_schema()
        reply = client.chat.completions.create(
            model=OLLAMA_MODEL, max_tokens=max_tokens,
            response_format={"type": "json_schema", "json_schema": {"name": shape.__name__, "schema": schema}},
            messages=[{"role": "system", "content": system + "\nReply with JSON matching this schema:\n"
                       + json.dumps(schema)},
                      {"role": "user", "content": prompt}])
        return shape.model_validate_json(_json_part(reply.choices[0].message.content or ""))
    reply = client.beta.messages.parse(model=CLAUDE_MODEL, max_tokens=max_tokens, system=system,
                                       output_format=shape, messages=[{"role": "user", "content": prompt}],
                                       **_claude_extras())
    if reply.stop_reason == "refusal":
        raise RuntimeError("The model declined this request.")
    return reply.parsed_output
