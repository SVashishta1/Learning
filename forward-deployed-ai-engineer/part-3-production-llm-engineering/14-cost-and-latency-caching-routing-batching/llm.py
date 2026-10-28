"""llm.py: ONE small door to a language model. Every lesson in Parts 3 and 4 has this same file.

Claude (the default)
    pip install anthropic
    export ANTHROPIC_API_KEY=sk-ant-...            (Windows PowerShell: $env:ANTHROPIC_API_KEY="sk-ant-...")
    optional: export CLAUDE_MODEL=claude-haiku-5-5  (much cheaper while you learn; default is claude-opus-5-5)
A local open model through Ollama (free, private, no key)
    install Ollama, run `ollama pull qwen3:8b`, then:  export LLM_PROVIDER=ollama
    optional: export OLLAMA_MODEL=llama3.1:8b        (any model you have pulled; tool calls need a tool-capable model)

Every call returns a Reply (text, tool calls, tokens, cost, seconds), so the lessons never care which model answered.
Messages use ONE simple shape for both providers:
    {"role": "user", "content": "text"}
    {"role": "assistant", "content": "text", "tool_calls": [{"id": "...", "name": "...", "args": {...}}]}  <- reply.message
    {"role": "tool", "id": "<the tool call's id>", "content": "result text", "is_error": False}
"""
import json
import os
import time
from dataclasses import dataclass, field

PROVIDER = os.getenv("LLM_PROVIDER", "claude")                 # "claude" or "ollama"
MODEL = os.getenv("CLAUDE_MODEL", "claude-opus-5-5")             # the strong default model
CHEAP_MODEL = os.getenv("CHEAP_MODEL", "claude-haiku-5-5")       # used for simple, high-volume jobs
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/v1")  # Ollama's OpenAI-compatible API
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen3:8b")

# $ per 1 million tokens: (input, output, cache read). Cache WRITES cost 1.25 x input. Local models cost $0.
# Check current prices: https://platform.claude.com/docs/en/about-claude/pricing
PRICES = {"claude-opus-5-5": (4.00, 20.00, 0.20), "claude-sonnet-5-5": (2.00, 10.00, 0.20),
          "claude-haiku-5-5": (0.10, 0.50, 0.01)}
# On these models we switch on "server-side fallback": if a safety check declines a request,
# the API retries it on a fallback model inside the same call.
_FALLBACK_MODELS = {"claude-opus-5-5", "claude-opus-5", "claude-fable-5-1", "claude-sonnet-5-5"}
KEY_HELP = ("Set ANTHROPIC_API_KEY (see the Part 3 README), or run the lesson's --offline mode, "
            "or use a local model with LLM_PROVIDER=ollama.")

_claude_client = None


def set_client(client):
    """Use a different Claude client (tests and --offline demos pass a fake one here)."""
    global _claude_client
    _claude_client = client


def claude_client():
    global _claude_client
    if _claude_client is None:
        import anthropic
        try:
            _claude_client = anthropic.Anthropic()          # reads ANTHROPIC_API_KEY from the environment
        except Exception as e:                             # no key / no login found
            raise SystemExit(f"❌ Could not create the Claude client ({e}). {KEY_HELP}")
    return _claude_client


def cost_usd(model, input_tokens=0, output_tokens=0, cache_read=0, cache_write=0) -> float:
    p_in, p_out, p_read = PRICES.get(model, (0.0, 0.0, 0.0))
    return (input_tokens * p_in + output_tokens * p_out + cache_read * p_read + cache_write * p_in * 1.25) / 1e6


@dataclass
class Reply:
    text: str
    tool_calls: list = field(default_factory=list)   # [{"id", "name", "args"}]
    parsed: object = None                             # filled when you pass schema=SomePydanticModel
    model: str = ""
    stop_reason: str = ""
    input_tokens: int = 0
    output_tokens: int = 0
    cache_read_tokens: int = 0
    cache_write_tokens: int = 0
    seconds: float = 0.0
    message: dict = field(default_factory=dict)      # append this to your messages list to continue the chat

    @property
    def cost_usd(self) -> float:
        return cost_usd(self.model, self.input_tokens, self.output_tokens, self.cache_read_tokens, self.cache_write_tokens)


def chat(messages, *, system="", model=None, tools=None, schema=None, max_tokens=4000, effort=None, cache=False) -> Reply:
    """Send a conversation, get a Reply.
    messages: a string, or a list of messages in the shape described at the top of this file.
    tools:    [{"name", "description", "input_schema"}] (Claude's tool format; converted for Ollama).
    schema:   a Pydantic model class -> the model must answer in that exact shape; result in reply.parsed.
    effort:   "low" | "medium" | "high" ... how hard Claude thinks (ignored by Ollama).
    cache:    True marks the system prompt for prompt caching (Claude only; see lesson 14).
    """
    if isinstance(messages, str):
        messages = [{"role": "user", "content": messages}]
    start = time.perf_counter()
    if PROVIDER == "ollama":
        reply = _ollama_chat(messages, system, model or OLLAMA_MODEL, tools, schema, max_tokens)
    else:
        reply = _claude_chat(messages, system, model or MODEL, tools, schema, max_tokens, effort, cache)
    reply.seconds = time.perf_counter() - start
    if schema is not None:
        reply.parsed = schema.model_validate_json(reply.text)   # raises if the JSON doesn't fit the shape
    return reply


def stream(messages, *, system="", model=None, max_tokens=4000, effort=None):
    """Like chat(), but yields the answer piece by piece while it is being written."""
    if isinstance(messages, str):
        messages = [{"role": "user", "content": messages}]
    if PROVIDER == "ollama":
        yield from _ollama_stream(messages, system, model or OLLAMA_MODEL, max_tokens)
        return
    import anthropic
    model = model or MODEL
    kwargs = _claude_kwargs(messages, system, model, None, None, max_tokens, effort, False)
    try:
        with claude_client().beta.messages.stream(**kwargs) as live:
            yield from live.text_stream
    except anthropic.AuthenticationError:
        raise SystemExit("❌ Your API key is wrong or was deleted. " + KEY_HELP)


# ----------------------------------------------------------------- Claude ---------
def _dump(block) -> dict:
    """Turn an SDK content block into a plain dict (so it can be sent back, saved to a database, or printed)."""
    if hasattr(block, "model_dump"):
        return block.model_dump(exclude_none=True)
    return dict(vars(block)) if not isinstance(block, dict) else block


def _claude_messages(messages) -> list:
    out = []
    for m in messages:
        if m["role"] == "tool":
            block = {"type": "tool_result", "tool_use_id": m["id"], "content": m["content"]}
            if m.get("is_error"):
                block["is_error"] = True
            previous = out[-1] if out else None
            if previous and previous["role"] == "user" and isinstance(previous["content"], list) \
                    and all(b.get("type") == "tool_result" for b in previous["content"]):
                previous["content"].append(block)    # parallel tool results must share ONE user message
            else:
                out.append({"role": "user", "content": [block]})
        elif m["role"] == "assistant":
            if m.get("raw"):                          # Claude's own blocks (keeps its thinking blocks intact)
                out.append({"role": "assistant", "content": m["raw"]})
            else:
                blocks = [{"type": "text", "text": m["content"]}] if m.get("content") else []
                blocks += [{"type": "tool_use", "id": c["id"], "name": c["name"], "input": c["args"]}
                           for c in m.get("tool_calls", [])]
                out.append({"role": "assistant", "content": blocks})
        else:
            out.append({"role": m["role"], "content": m["content"]})
    return out


def _claude_kwargs(messages, system, model, tools, schema, max_tokens, effort, cache) -> dict:
    kwargs = {"model": model, "max_tokens": max_tokens, "messages": _claude_messages(messages)}
    if system:
        block = {"type": "text", "text": system}
        if cache:
            block["cache_control"] = {"type": "ephemeral"}   # "remember this prefix for ~5 minutes"
        kwargs["system"] = [block]
    if tools:
        kwargs["tools"] = tools
    output_config = {}
    if effort:
        output_config["effort"] = effort
    if schema is not None:
        import anthropic
        output_config["format"] = {"type": "json_schema", "schema": anthropic.transform_schema(schema)}
    if output_config:
        kwargs["output_config"] = output_config
    if model in _FALLBACK_MODELS:
        kwargs |= {"betas": ["server-side-fallback-2026-07-01"], "fallbacks": "default"}
    return kwargs


def _claude_chat(messages, system, model, tools, schema, max_tokens, effort, cache) -> Reply:
    import anthropic
    kwargs = _claude_kwargs(messages, system, model, tools, schema, max_tokens, effort, cache)
    try:
        response = claude_client().beta.messages.create(**kwargs)
    except anthropic.AuthenticationError:
        raise SystemExit("❌ Your API key is wrong or was deleted. " + KEY_HELP)
    if response.stop_reason == "refusal":
        raise RuntimeError("The model declined this request (stop_reason='refusal').")
    text = "".join(b.text for b in response.content if b.type == "text")
    calls = [{"id": b.id, "name": b.name, "args": dict(b.input)} for b in response.content if b.type == "tool_use"]
    usage = response.usage
    return Reply(text=text, tool_calls=calls, model=model, stop_reason=response.stop_reason,
                 input_tokens=usage.input_tokens, output_tokens=usage.output_tokens,
                 cache_read_tokens=getattr(usage, "cache_read_input_tokens", 0) or 0,
                 cache_write_tokens=getattr(usage, "cache_creation_input_tokens", 0) or 0,
                 message={"role": "assistant", "content": text, "tool_calls": calls,
                          "raw": [_dump(b) for b in response.content]})


# ----------------------------------------------------------------- Ollama ---------
def _openai_messages(messages, system) -> list:
    out = [{"role": "system", "content": system}] if system else []
    for m in messages:
        if m["role"] == "tool":
            out.append({"role": "tool", "tool_call_id": m["id"], "content": m["content"]})
        elif m["role"] == "assistant":
            msg = {"role": "assistant", "content": m.get("content", "")}
            if m.get("tool_calls"):
                msg["tool_calls"] = [{"id": c["id"], "type": "function",
                                      "function": {"name": c["name"], "arguments": json.dumps(c["args"])}}
                                     for c in m["tool_calls"]]
            out.append(msg)
        else:
            content = m["content"]
            if isinstance(content, list):             # Claude-style blocks -> plain text for local models
                content = "\n".join(b.get("text", "") for b in content if isinstance(b, dict))
            out.append({"role": m["role"], "content": content})
    return out


def _ollama_request(messages, system, model, tools, schema, max_tokens, stream=False) -> dict:
    body = {"model": model, "messages": _openai_messages(messages, system), "max_tokens": max_tokens, "stream": stream}
    if tools:
        body["tools"] = [{"type": "function", "function": {"name": t["name"], "description": t.get("description", ""),
                                                            "parameters": t["input_schema"]}} for t in tools]
    if schema is not None:
        body["response_format"] = {"type": "json_schema",
                                   "json_schema": {"name": schema.__name__, "schema": schema.model_json_schema()}}
    return body


def _ollama_chat(messages, system, model, tools, schema, max_tokens) -> Reply:
    import httpx
    try:
        r = httpx.post(f"{OLLAMA_URL}/chat/completions", timeout=300,
                       json=_ollama_request(messages, system, model, tools, schema, max_tokens))
    except httpx.ConnectError:
        raise SystemExit(f"❌ Can't reach Ollama at {OLLAMA_URL}. Start it (open the Ollama app or run `ollama serve`).")
    r.raise_for_status()
    return _from_openai(r.json(), model)


def _from_openai(data: dict, model: str) -> Reply:
    choice = data["choices"][0]
    msg = choice["message"]
    calls = [{"id": c.get("id") or f"call_{i}", "name": c["function"]["name"],
              "args": json.loads(c["function"]["arguments"] or "{}")} for i, c in enumerate(msg.get("tool_calls") or [])]
    usage = data.get("usage") or {}
    stop = "tool_use" if calls else {"length": "max_tokens"}.get(choice.get("finish_reason"), "end_turn")
    text = msg.get("content") or ""
    return Reply(text=text, tool_calls=calls, model=model, stop_reason=stop,
                 input_tokens=usage.get("prompt_tokens", 0), output_tokens=usage.get("completion_tokens", 0),
                 message={"role": "assistant", "content": text, "tool_calls": calls})


def _ollama_stream(messages, system, model, max_tokens):
    import httpx
    body = _ollama_request(messages, system, model, None, None, max_tokens, stream=True)
    with httpx.stream("POST", f"{OLLAMA_URL}/chat/completions", json=body, timeout=300) as r:
        for line in r.iter_lines():                  # server-sent events: lines that start with "data: "
            if line.startswith("data: ") and line != "data: [DONE]":
                delta = json.loads(line[6:])["choices"][0]["delta"].get("content")
                if delta:
                    yield delta
