"""fake_llm.py: a pretend Claude client for tests and --offline demos. No API key, no cost, same answer every time.

It has the same shape as anthropic.Anthropic(): client.beta.messages.create(...) returns an object with
.content, .stop_reason and .usage, exactly like the real response. Give it either:
  * a list of replies (each call returns the next one), or
  * a responder function  responder(request_kwargs) -> reply  (to make "smart" fakes that react to the prompt).
"""
import json
from types import SimpleNamespace as NS


def _usage(input_tokens=120, output_tokens=40, cache_read=0, cache_write=0):
    return NS(input_tokens=input_tokens, output_tokens=output_tokens,
              cache_read_input_tokens=cache_read, cache_creation_input_tokens=cache_write)


def text_reply(text, input_tokens=120, output_tokens=40, cache_read=0, cache_write=0):
    """A normal answer."""
    return NS(content=[NS(type="text", text=text)], stop_reason="end_turn",
              usage=_usage(input_tokens, output_tokens, cache_read, cache_write))


def json_reply(obj, **usage):
    """A structured-output answer: the text is JSON."""
    return text_reply(json.dumps(obj), **usage)


def tool_reply(name, args, call_id="call_1", text=""):
    """The model asks to use ONE tool."""
    return tool_calls_reply([(name, args, call_id)], text)


def tool_calls_reply(calls, text=""):
    """The model asks to use several tools at once: calls = [(name, args, call_id), ...]."""
    blocks = ([NS(type="text", text=text)] if text else [])
    blocks += [NS(type="tool_use", id=call_id, name=name, input=args) for name, args, call_id in calls]
    return NS(content=blocks, stop_reason="tool_use", usage=_usage())


class FakeClaude:
    def __init__(self, replies=None, responder=None):
        self.replies, self.responder, self.calls = list(replies or []), responder, []
        self.beta = NS(messages=NS(create=self._create, stream=self._stream))
        self.messages = NS(create=self._create, count_tokens=self._count_tokens)

    def _create(self, **kwargs):
        self.calls.append(kwargs)                       # tests can look at exactly what was sent
        if self.responder:
            return self.responder(kwargs)
        return self.replies.pop(0) if self.replies else text_reply("ok")

    def _count_tokens(self, **kwargs):
        chars = len(json.dumps(kwargs.get("messages", []))) + len(json.dumps(kwargs.get("system", "")))
        return NS(input_tokens=chars // 4)

    def _stream(self, **kwargs):
        reply = self._create(**kwargs)
        words = "".join(b.text for b in reply.content if b.type == "text").split(" ")

        class _Live:
            text_stream = iter([w if i == 0 else " " + w for i, w in enumerate(words)])
            def __enter__(self): return self
            def __exit__(self, *exc): return False
            def get_final_message(self): return reply
        return _Live()


def last_user_text(kwargs) -> str:
    """Helper for responders: the text of the newest user message in a request."""
    for m in reversed(kwargs["messages"]):
        if m["role"] == "user":
            c = m["content"]
            return c if isinstance(c, str) else " ".join(str(b.get("content", b.get("text", ""))) for b in c)
    return ""
