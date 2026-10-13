"""A fake Claude client for tests: no API key, no cost, deterministic.
You give it a list of scripted replies; each call to create() returns the next one."""
from types import SimpleNamespace as NS


def text_reply(text, stop_reason="end_turn"):
    return NS(content=[NS(type="text", text=text)], stop_reason=stop_reason,
              usage=NS(input_tokens=100, output_tokens=50))


def tool_reply(name, args, call_id="call_1", text=""):
    blocks = ([NS(type="text", text=text)] if text else []) + [NS(type="tool_use", id=call_id, name=name, input=args)]
    return NS(content=blocks, stop_reason="tool_use", usage=NS(input_tokens=100, output_tokens=50))


class FakeClient:
    def __init__(self, replies=None, parsed=None):
        self.replies, self.parsed, self.calls = list(replies or []), list(parsed or []), []
        self.beta = NS(messages=NS(create=self._create, parse=self._parse, stream=self._stream))

    def _create(self, **kwargs):
        self.calls.append(kwargs)
        return self.replies.pop(0) if self.replies else text_reply("ok")

    def _parse(self, **kwargs):
        self.calls.append(kwargs)
        return NS(parsed_output=self.parsed.pop(0), stop_reason="end_turn", content=[], usage=NS(input_tokens=100, output_tokens=50))

    def _stream(self, **kwargs):
        reply = self._create(**kwargs)
        text = "".join(b.text for b in reply.content if b.type == "text")

        class _S:
            def __enter__(s): return s
            def __exit__(s, *a): return False
            text_stream = iter([w + " " for w in text.split()])
            def get_final_message(s): return reply
        return _S()
