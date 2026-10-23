"""Tests for llm.py, the helper every lesson in Parts 3-4 shares. Offline: Claude is faked, Ollama is never called."""
from pydantic import BaseModel

import llm
from fake_llm import FakeClaude, json_reply, text_reply, tool_calls_reply


class City(BaseModel):
    name: str
    country: str


def test_text_reply_tokens_and_cost():
    llm.set_client(FakeClaude([text_reply("Hello!", input_tokens=1000, output_tokens=100)]))
    reply = llm.chat("Hi", model="claude-opus-5-5")
    assert reply.text == "Hello!" and reply.message["role"] == "assistant"
    assert round(reply.cost_usd, 6) == round((1000 * 4 + 100 * 20) / 1e6, 6)


def test_schema_becomes_output_config_format_and_parsed():
    fake = FakeClaude([json_reply({"name": "Leeds", "country": "UK"})])
    llm.set_client(fake)
    reply = llm.chat("Where is our northern hub?", schema=City, effort="low")
    assert reply.parsed == City(name="Leeds", country="UK")
    cfg = fake.calls[0]["output_config"]
    assert cfg["effort"] == "low" and cfg["format"]["schema"]["additionalProperties"] is False


def test_cache_flag_marks_the_system_prompt():
    fake = FakeClaude()
    llm.set_client(fake)
    llm.chat("Hi", system="Long stable rules...", cache=True)
    assert fake.calls[0]["system"][0]["cache_control"] == {"type": "ephemeral"}


def test_parallel_tool_results_are_grouped_into_one_user_message():
    fake = FakeClaude([tool_calls_reply([("a", {}, "c1"), ("b", {}, "c2")]), text_reply("done")])
    llm.set_client(fake)
    first = llm.chat("do two things", tools=[{"name": "a", "description": "", "input_schema": {"type": "object"}}])
    messages = [{"role": "user", "content": "do two things"}, first.message,
                {"role": "tool", "id": "c1", "content": "A ok"}, {"role": "tool", "id": "c2", "content": "B failed", "is_error": True}]
    llm.chat(messages)
    sent = fake.calls[1]["messages"]
    assert len(sent) == 3 and [b["tool_use_id"] for b in sent[2]["content"]] == ["c1", "c2"]
    assert sent[2]["content"][1]["is_error"] is True
    assert sent[1]["content"][0]["type"] == "tool_use"          # Claude's own blocks were sent back unchanged


def test_openai_format_conversion_for_ollama():
    messages = [{"role": "user", "content": "hi"},
                {"role": "assistant", "content": "", "tool_calls": [{"id": "x1", "name": "get", "args": {"id": 7}}]},
                {"role": "tool", "id": "x1", "content": "found"}]
    out = llm._openai_messages(messages, "be brief")
    assert out[0] == {"role": "system", "content": "be brief"}
    assert out[2]["tool_calls"][0]["function"] == {"name": "get", "arguments": '{"id": 7}'}
    assert out[3] == {"role": "tool", "tool_call_id": "x1", "content": "found"}
    reply = llm._from_openai({"choices": [{"finish_reason": "tool_calls", "message": {"content": "", "tool_calls": [
        {"id": "y", "function": {"name": "get", "arguments": '{"id": 8}'}}]}}],
        "usage": {"prompt_tokens": 50, "completion_tokens": 5}}, "qwen3:8b")
    assert reply.tool_calls == [{"id": "y", "name": "get", "args": {"id": 8}}] and reply.stop_reason == "tool_use"
    assert reply.cost_usd == 0                                     # local models are free to run


def test_stream_yields_pieces():
    llm.set_client(FakeClaude([text_reply("one two three")]))
    assert "".join(llm.stream("count")) == "one two three"
