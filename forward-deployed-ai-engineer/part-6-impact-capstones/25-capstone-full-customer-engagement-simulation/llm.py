"""llm.py: one small door to three kinds of "brain". Read it once; every agent uses it.

  LLM_PROVIDER=anthropic   Claude through the official anthropic SDK (the default; needs ANTHROPIC_API_KEY)
  LLM_PROVIDER=ollama      any OpenAI-compatible server: Ollama (default URL), vLLM, llama.cpp's server
  FAKE_LLM=1               no model at all: each agent's small rule-based stand-in (tests, demos, CI, no key)

Agents only ever call `provider.call(...)`, so they never know which brain they have.
That is what lets one team run on Claude, on a laptop with open models, or fully offline.
"""
import json
import os
import uuid
from dataclasses import dataclass, field

# --- settings (read from environment variables, so Docker/compose can change them) ---
HEAD_MODEL = os.getenv("CLAUDE_MODEL", "claude-opus-5-5")             # the head agent: the best model
SPECIALIST_MODEL = os.getenv("SPECIALIST_MODEL", "claude-haiku-5-5")  # specialists: the cheap, fast model
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:7b")                # a small open model that can call tools
OLLAMA_HEAD_MODEL = os.getenv("OLLAMA_HEAD_MODEL", OLLAMA_MODEL)       # optionally a bigger one for the head

# On these Claude models we switch on "server-side fallback": if a request is ever declined by a
# safety classifier, the API retries it on a fallback model inside the same call.
_FALLBACK_MODELS = {"claude-opus-5-5", "claude-opus-5", "claude-fable-5-1", "claude-sonnet-5-5"}


@dataclass
class ToolSpec:
    """A tool as the model sees it: a name, a sentence about when to use it, and a JSON schema for its inputs."""
    name: str
    description: str
    parameters: dict


@dataclass
class ToolCall:
    id: str
    name: str
    args: dict


@dataclass
class Reply:
    """One answer from any brain, in one shape: some text, maybe some tool calls, and token counts."""
    text: str = ""
    tool_calls: list[ToolCall] = field(default_factory=list)
    input_tokens: int = 0
    output_tokens: int = 0
    assistant_message: object = None      # the provider's own format, appended to the history as-is


def provider_name() -> str:
    if os.getenv("FAKE_LLM", "").lower() in {"1", "true", "yes"}:
        return "fake"
    return os.getenv("LLM_PROVIDER", "anthropic").lower()


# ---------------------------------------------------------------- Claude (Anthropic SDK)
class AnthropicProvider:
    name = "anthropic"

    def __init__(self, client=None):
        if client is None:
            import anthropic
            if not os.getenv("ANTHROPIC_API_KEY"):
                raise SystemExit("ANTHROPIC_API_KEY is not set. Set it, or run with FAKE_LLM=1 (no key needed), "
                                 "or LLM_PROVIDER=ollama for a local model.")
            client = anthropic.Anthropic()            # reads ANTHROPIC_API_KEY from the environment
        self.client = client

    def model_for(self, role: str) -> str:
        return HEAD_MODEL if role == "head" else SPECIALIST_MODEL

    def start(self, task: str) -> list:
        return [{"role": "user", "content": task}]

    def user(self, text: str) -> dict:
        return {"role": "user", "content": text}

    def tool_results(self, results: list[tuple[str, str, bool]]) -> list:
        # Claude wants ALL results of one turn together, in ONE user message.
        return [{"role": "user", "content": [
            {"type": "tool_result", "tool_use_id": cid, "content": content, "is_error": is_error}
            for cid, content, is_error in results]}]

    def call(self, *, system, messages, tools, model, effort="medium", fake_brain=None) -> Reply:
        extras = {"betas": ["server-side-fallback-2026-07-01"], "fallbacks": "default"} if model in _FALLBACK_MODELS else {}
        response = self.client.beta.messages.create(
            model=model, max_tokens=16000, system=system, messages=messages,
            tools=[{"name": t.name, "description": t.description, "input_schema": t.parameters} for t in tools],
            output_config={"effort": effort}, **extras)
        if response.stop_reason == "refusal":
            raise RuntimeError("The model declined this request.")
        text = "".join(b.text for b in response.content if b.type == "text")
        calls = [ToolCall(b.id, b.name, dict(b.input)) for b in response.content if b.type == "tool_use"]
        return Reply(text, calls, response.usage.input_tokens, response.usage.output_tokens,
                     {"role": "assistant", "content": response.content})   # keep every block (thinking too)


# ---------------------------------------------------------------- Ollama / vLLM / any OpenAI-compatible server
class OpenAICompatProvider:
    """Talks the OpenAI "chat completions" format over plain HTTP. Ollama serves it at /v1 on port 11434."""
    name = "ollama"

    def __init__(self, base_url: str = "", http=None):
        import httpx
        self.base_url = (base_url or OLLAMA_BASE_URL).rstrip("/")
        self.http = http or httpx.Client(timeout=600)          # local models can be slow on a laptop
        self.api_key = os.getenv("OPENAI_COMPAT_API_KEY", "ollama")   # Ollama ignores it; vLLM may need one

    def model_for(self, role: str) -> str:
        return OLLAMA_HEAD_MODEL if role == "head" else OLLAMA_MODEL

    def start(self, task: str) -> list:
        return [{"role": "user", "content": task}]

    def user(self, text: str) -> dict:
        return {"role": "user", "content": text}

    def tool_results(self, results: list[tuple[str, str, bool]]) -> list:
        # The OpenAI format wants one "tool" message per result.
        return [{"role": "tool", "tool_call_id": cid, "content": ("ERROR: " if err else "") + content}
                for cid, content, err in results]

    def call(self, *, system, messages, tools, model, effort="medium", fake_brain=None) -> Reply:
        body = {"model": model, "messages": [{"role": "system", "content": system}] + messages,
                "tools": [{"type": "function", "function": {"name": t.name, "description": t.description,
                                                            "parameters": t.parameters}} for t in tools]}
        r = self.http.post(f"{self.base_url}/chat/completions", json=body,
                           headers={"Authorization": f"Bearer {self.api_key}"})
        r.raise_for_status()
        data = r.json()
        msg = data["choices"][0]["message"]
        calls = []
        for c in msg.get("tool_calls") or []:
            raw = c["function"].get("arguments") or "{}"
            try:
                args = raw if isinstance(raw, dict) else json.loads(raw)   # usually a JSON *string*
            except json.JSONDecodeError:
                args = {"__invalid_json__": raw}                           # the agent will report it back
            calls.append(ToolCall(c.get("id") or uuid.uuid4().hex[:8], c["function"]["name"], args))
        assistant = {"role": "assistant", "content": msg.get("content") or ""}
        if msg.get("tool_calls"):
            assistant["tool_calls"] = msg["tool_calls"]
        usage = data.get("usage") or {}
        return Reply(msg.get("content") or "", calls, usage.get("prompt_tokens", 0),
                     usage.get("completion_tokens", 0), assistant)


# ---------------------------------------------------------------- FAKE: no model, rule-based stand-ins
@dataclass
class FakeView:
    """What a fake brain can see: the task, and every tool call it has made so far with the results."""
    task: str
    history: list[dict]          # [{"name", "args", "output", "is_error"}, ...] in order
    step: int

    def outputs(self, name: str) -> list:
        """All (JSON-decoded when possible) results of one tool, oldest first."""
        found = []
        for h in self.history:
            if h["name"] == name and not h["is_error"]:
                try:
                    found.append(json.loads(h["output"]))
                except json.JSONDecodeError:
                    found.append(h["output"])
        return found

    def called(self, name: str) -> bool:
        return any(h["name"] == name for h in self.history)

    def last_error(self) -> str:
        return self.history[-1]["output"] if self.history and self.history[-1]["is_error"] else ""


def use_tools(*calls: tuple[str, dict], text: str = "") -> Reply:
    """Helper for fake brains: 'call these tools now'."""
    return Reply(text=text, tool_calls=[ToolCall(f"fake_{uuid.uuid4().hex[:6]}", n, a) for n, a in calls])


def use_tool(name: str, **args) -> Reply:
    return use_tools((name, args))


def say(text: str) -> Reply:
    return Reply(text=text)


class FakeProvider:
    """Plays the model's part with each agent's `fake_brain` function. Free, instant and repeatable.
    It also remembers everything that was 'sent to the model', so tests can check what would leave the building."""
    name = "fake"

    def __init__(self):
        self.sent: list[dict] = []

    def model_for(self, role: str) -> str:
        return "fake-head" if role == "head" else "fake-specialist"

    def start(self, task: str) -> list:
        return [{"role": "user", "content": task}]

    def user(self, text: str) -> dict:
        return {"role": "user", "content": text}

    def tool_results(self, results: list[tuple[str, str, bool]]) -> list:
        return [{"role": "tool", "results": results}]

    def call(self, *, system, messages, tools, model, effort="medium", fake_brain=None) -> Reply:
        self.sent.append({"system": system, "messages": json.dumps(messages, default=str)})
        history, pending = [], {}
        for m in messages:
            if m["role"] == "assistant":
                for c in m.get("tool_calls", []):
                    pending[c.id] = c
            elif m["role"] == "tool":
                for cid, content, is_error in m["results"]:
                    c = pending.get(cid)
                    history.append({"name": c.name if c else "?", "args": c.args if c else {},
                                    "output": content, "is_error": is_error})
        view = FakeView(task=messages[0]["content"], history=history,
                        step=sum(1 for m in messages if m["role"] == "assistant"))
        reply = fake_brain(view)
        # rough token estimate (4 characters ~ 1 token) so budgets and cost reports still work in FAKE mode
        reply.input_tokens = (len(system) + len(self.sent[-1]["messages"])) // 4
        reply.output_tokens = max(1, len(json.dumps([c.args for c in reply.tool_calls]) + reply.text) // 4)
        reply.assistant_message = {"role": "assistant", "text": reply.text, "tool_calls": reply.tool_calls}
        return reply


def get_provider():
    name = provider_name()
    if name == "fake":
        return FakeProvider()
    if name in {"ollama", "openai", "vllm", "local"}:
        return OpenAICompatProvider()
    if name == "anthropic":
        return AnthropicProvider()
    raise SystemExit(f"Unknown LLM_PROVIDER={name!r}. Use anthropic, ollama, or set FAKE_LLM=1.")
