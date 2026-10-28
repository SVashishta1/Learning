"""The agent engine: loop, report checks, budgets, approvals, and the two real providers (stubbed)."""
import json
from types import SimpleNamespace as NS

import httpx
from pydantic import BaseModel

from agent_core import Agent, Budget, Mission, NoArgs, Tool, run_mission
from llm import AnthropicProvider, FakeProvider, OpenAICompatProvider, say, use_tool


class Answer(BaseModel):
    total: int


def adder_agent(brain, **kw):
    tools = [Tool("add", "Add two numbers.", type("AddArgs", (BaseModel,), {"__annotations__": {"a": int, "b": int}}),
                  lambda a, b: a + b)]
    return Agent("adder", "adds", "You add.", tools, Answer, brain, **kw)


def test_loop_tools_then_report():
    def brain(view):
        return use_tool("add", a=2, b=3) if not view.called("add") else use_tool("submit_report", total=view.outputs("add")[0])
    r = adder_agent(brain).run("2+3?", Mission("t"), FakeProvider())
    assert (r.status, r.report) == ("done", {"total": 5})


def test_bad_report_is_sent_back_with_the_problems():
    def brain(view):
        if view.step == 0:
            return use_tool("submit_report", total=-1)
        assert "must be positive" in view.last_error()                   # the agent SEES why it was rejected
        return use_tool("submit_report", total=5)
    agent = adder_agent(brain, check=lambda rep, m: ["total must be positive"] if rep.total < 0 else [])
    assert agent.run("x", Mission("t"), FakeProvider()).report == {"total": 5}


def test_step_limit_and_prose_nudge():
    r = adder_agent(lambda view: say("I think it is 5"), max_steps=3).run("x", Mission("t"), FakeProvider())
    assert r.status == "step_limit"


def test_budget_stops_the_agent():
    m = Mission("t", Budget(max_tool_calls=2))
    r = adder_agent(lambda view: use_tool("add", a=1, b=1)).run("x", m, FakeProvider())
    assert r.status == "budget_exceeded"


def test_actions_need_a_named_human_and_only_approved_ones_run():
    m = Mission("t")
    ran = []
    a1 = m.propose("x", "dispatch", "send truck", {}, lambda: ran.append("a1") or "sent")
    a2 = m.propose("x", "dispatch", "send boat", {}, lambda: ran.append("a2") or "sent")
    try:
        m.decide(a1.id, True, by="  ")
        raise AssertionError("an anonymous approval must fail")
    except ValueError:
        pass
    m.decide(a1.id, True, by="Sam")
    m.decide(a2.id, False, by="Sam", note="boat needed elsewhere")
    m.execute_approved()
    m.execute_approved()                                                  # running twice must not repeat it
    assert ran == ["a1"] and m.action("A2").status == "rejected"


def test_head_delegates_to_specialist():
    spec = adder_agent(lambda v: use_tool("submit_report", total=7))
    head = Agent("boss", "leads", "Lead.", [], Answer,
                 lambda v: use_tool("ask_adder", task="add") if not v.called("ask_adder")
                 else use_tool("submit_report", total=v.outputs("ask_adder")[0]["report"]["total"]), role="head")
    m = run_mission(head, [spec], Mission("t"), FakeProvider(), "go")
    assert m.plan == {"total": 7} and m.reports["adder"]["status"] == "done" and m.status == "completed"


# ---------- Claude, with a fake client shaped like the real SDK response
def anthropic_response(blocks, stop):
    return NS(content=blocks, stop_reason=stop, usage=NS(input_tokens=1000, output_tokens=200))


def test_anthropic_provider_round_trip():
    replies = [anthropic_response([NS(type="thinking", thinking=""), NS(type="tool_use", id="t1", name="add", input={"a": 2, "b": 3})], "tool_use"),
               anthropic_response([NS(type="text", text="Done."), NS(type="tool_use", id="t2", name="submit_report", input={"total": 5})], "tool_use")]
    sent = []
    def create(**kw):
        sent.append({**kw, "messages": list(kw["messages"])})          # snapshot: the agent keeps appending
        return replies.pop(0)
    client = NS(beta=NS(messages=NS(create=create)))
    m = Mission("t")
    r = adder_agent(None).run("2+3?", m, AnthropicProvider(client=client))
    assert r.report == {"total": 5}
    assert sent[0]["model"] == "claude-haiku-5-5" and sent[0]["output_config"] == {"effort": "medium"}
    assert sent[0]["tools"][-1]["name"] == "submit_report"
    second = sent[1]["messages"]
    assert second[-1]["content"][0] == {"type": "tool_result", "tool_use_id": "t1", "content": "5", "is_error": False}
    assert m.budget.usd > 0                                              # haiku prices were applied


# ---------- Ollama / vLLM, with a fake HTTP server
def test_openai_compatible_provider_round_trip():
    calls = []

    def handler(request):
        body = json.loads(request.content)
        calls.append(body)
        if len(calls) == 1:
            tc = [{"id": "c1", "type": "function", "function": {"name": "add", "arguments": "{\"a\": 4, \"b\": 4}"}}]
        else:
            tc = [{"id": "c2", "type": "function", "function": {"name": "submit_report", "arguments": "{\"total\": 8}"}}]
        return httpx.Response(200, json={"choices": [{"message": {"role": "assistant", "content": "", "tool_calls": tc}}],
                                         "usage": {"prompt_tokens": 50, "completion_tokens": 10}})
    http = httpx.Client(transport=httpx.MockTransport(handler))
    r = adder_agent(None).run("4+4?", Mission("t"), OpenAICompatProvider("http://ollama:11434/v1", http=http))
    assert r.report == {"total": 8}
    assert calls[0]["messages"][0]["role"] == "system" and calls[0]["tools"][0]["type"] == "function"
    assert calls[1]["messages"][-1] == {"role": "tool", "tool_call_id": "c1", "content": "8"}
