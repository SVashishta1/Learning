# fake_llm.py: pretend AI clients for tests. No API key, no internet, no cost, same answer every time.
# They have the same "shape" as the real clients, so llm.py cannot tell the difference.
from types import SimpleNamespace as NS


class FakeClaude:
    """Looks like anthropic.Anthropic(): has .beta.messages.create(...) and .beta.messages.parse(...)."""

    def __init__(self, text="ok", parsed=None):
        self.text, self.parsed, self.calls = text, parsed, []
        self.beta = NS(messages=NS(create=self._create, parse=self._parse))

    def _create(self, **kwargs):
        self.calls.append(kwargs)                                   # remember what was sent, so tests can check it
        return NS(stop_reason="end_turn", content=[NS(type="text", text=self.text)])

    def _parse(self, **kwargs):
        self.calls.append(kwargs)
        return NS(stop_reason="end_turn", content=[], parsed_output=self.parsed)


class FakeOllama:
    """Looks like openai.OpenAI(base_url=...ollama...): has .chat.completions.create(...)."""

    def __init__(self, text="ok"):
        self.text, self.calls = text, []
        self.chat = NS(completions=NS(create=self._create))

    def _create(self, **kwargs):
        self.calls.append(kwargs)
        return NS(choices=[NS(message=NS(content=self.text))])
