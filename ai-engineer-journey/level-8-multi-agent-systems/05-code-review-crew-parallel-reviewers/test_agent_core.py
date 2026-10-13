"""Tests for the shared agent core (fake LLM, offline)."""
from pydantic import BaseModel

from agent_core import Agent, Tool
from fake_llm import FakeClient, text_reply, tool_reply


class AddIn(BaseModel):
    a: int
    b: int


def make_agent(replies, approve=True, **kw):
    tool = Tool("add", "Add two ints", AddIn, lambda a, b: str(a + b), needs_approval=kw.pop("needs_approval", False))
    return Agent("tester", "test", tools=[tool], client=FakeClient(replies), verbose=False,
                 approver=lambda *a: approve, **kw)


def test_loop_runs_tool_and_finishes():
    agent = make_agent([tool_reply("add", {"a": 2, "b": 3}), text_reply("5")])
    assert agent.run("2+3?") == "5"
    assert agent.client.calls[1]["messages"][2]["content"][0]["content"] == "5"
    assert agent.input_tokens == 200


def test_declined_approval_is_reported_to_model():
    agent = make_agent([tool_reply("add", {"a": 1, "b": 1}), text_reply("ok, not doing it")], approve=False, needs_approval=True)
    agent.run("add")
    assert "DECLINED" in agent.client.calls[1]["messages"][2]["content"][0]["content"]


def test_invalid_args_become_errors():
    agent = make_agent([tool_reply("add", {"a": "two"}), text_reply("sorry")])
    agent.run("add")
    result = agent.client.calls[1]["messages"][2]["content"][0]
    assert result["is_error"] is True
