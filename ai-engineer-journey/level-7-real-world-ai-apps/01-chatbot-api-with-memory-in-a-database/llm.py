"""Tiny wrapper so every project calls Claude the same way. Read it once; it's short.

Setup:  pip install anthropic
        export ANTHROPIC_API_KEY=sk-ant-...        (get one at https://platform.claude.com)
Optional: export CLAUDE_MODEL=claude-haiku-5-5   (cheaper/faster while you experiment)
"""
import os

import anthropic

MODEL = os.getenv("CLAUDE_MODEL", "claude-opus-5-5")

# On these models we turn on "server-side fallback": if a request is ever declined by a safety classifier,
# the API automatically retries it on a fallback model inside the same call.
_FALLBACK_MODELS = {"claude-opus-5-5", "claude-opus-5", "claude-fable-5-1", "claude-sonnet-5-5"}


def get_client() -> anthropic.Anthropic:
    return anthropic.Anthropic()          # reads ANTHROPIC_API_KEY from the environment


def _extras(model: str) -> dict:
    return {"betas": ["server-side-fallback-2026-07-01"], "fallbacks": "default"} if model in _FALLBACK_MODELS else {}


def create(client, **kwargs):
    """Same arguments as client.messages.create (model defaults to MODEL)."""
    model = kwargs.pop("model", MODEL)
    return client.beta.messages.create(model=model, **_extras(model), **kwargs)


def parse(client, **kwargs):
    """Structured output: pass output_format=YourPydanticModel, get response.parsed_output back."""
    model = kwargs.pop("model", MODEL)
    return client.beta.messages.parse(model=model, **_extras(model), **kwargs)


def stream(client, **kwargs):
    """Streaming context manager: `with stream(client, ...) as s: for text in s.text_stream: ...`"""
    model = kwargs.pop("model", MODEL)
    return client.beta.messages.stream(model=model, **_extras(model), **kwargs)


def text_of(response) -> str:
    """Join the text blocks of a response. Raises if the request was declined."""
    if response.stop_reason == "refusal":
        raise RuntimeError("The model declined this request.")
    return "".join(block.text for block in response.content if block.type == "text")
