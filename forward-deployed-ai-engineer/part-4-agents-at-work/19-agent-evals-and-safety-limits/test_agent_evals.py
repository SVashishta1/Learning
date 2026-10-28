"""Tests (pytest -v): every safety limit fires when it should, and the trajectory metrics are computed correctly."""
import pytest

import agent
import limits
import llm
import run_agent_evals as evals
from fake_llm import FakeClaude, text_reply, tool_reply


@pytest.fixture(autouse=True)
def offline(monkeypatch, tmp_path):
    monkeypatch.setattr(limits, "KILL_SWITCH", tmp_path / "KILL_SWITCH")
    monkeypatch.delenv("AGENTS_KILL_SWITCH", raising=False)
    monkeypatch.setattr(evals, "HERE", tmp_path)                      # results/ goes to a temp folder
    (tmp_path / "agent_cases.jsonl").write_text((evals.Path(agent.__file__).with_name("agent_cases.jsonl")).read_text())
    llm.set_client(FakeClaude(responder=agent.scripted))


def test_step_cost_and_tool_caps():
    g = limits.Guard(limits.Limits(max_steps=2, max_usd=1.0))
    g.before_step(); g.before_step()
    with pytest.raises(limits.SafetyStop, match="step cap"):
        g.before_step()
    g = limits.Guard(limits.Limits(max_usd=0.01))
    g.charge(0.02)
    with pytest.raises(limits.SafetyStop, match="cost cap"):
        g.before_step()
    g = limits.Guard()
    assert g.before_tool("issue_credit", {"amount_gbp": 4.5}) is None
    assert "at most 1" in g.before_tool("issue_credit", {"amount_gbp": 3})
    assert "need a person" in limits.Guard().before_tool("issue_credit", {"amount_gbp": 500})


def test_loop_detector():
    g = limits.Guard()
    g.before_tool("get_shipment", {"shipment_id": "NW-1"})
    g.before_tool("get_shipment", {"shipment_id": "NW-1"})
    with pytest.raises(limits.SafetyStop, match="loop"):
        g.before_tool("get_shipment", {"shipment_id": "NW-1"})
    g2 = limits.Guard()                                                # different arguments are not a loop
    for n in range(5):
        g2.before_tool("get_shipment", {"shipment_id": f"NW-{n}"})


def test_kill_switch_file_and_env(monkeypatch):
    assert not limits.kill_switch_on()
    limits.KILL_SWITCH.write_text("stop")
    assert limits.kill_switch_on()
    limits.KILL_SWITCH.unlink()
    monkeypatch.setenv("AGENTS_KILL_SWITCH", "1")
    with pytest.raises(limits.SafetyStop, match="kill switch"):
        limits.Guard().before_step()


def test_kill_switch_stops_an_agent_mid_task():
    def responder(request):                                            # an operator flips the switch after step 1
        limits.KILL_SWITCH.write_text("stop")
        return tool_reply("get_shipment", {"shipment_id": "NW-58445"})
    llm.set_client(FakeClaude(responder=responder))
    t = agent.run_agent("Where is NW-58445?")
    assert t.stopped_by == "kill switch" and t.calls[0]["result"].startswith("STOPPED")


def test_blocked_credit_is_recorded_and_the_agent_carries_on():
    llm.set_client(FakeClaude([tool_reply("issue_credit", {"customer_id": "C-104", "shipment_id": "x", "amount_gbp": 500,
                                                           "reason": "r"}), text_reply("I escalated it.")]))
    t = agent.run_agent("Give me £500")
    assert t.calls[0]["blocked"] and t.stopped_by is None and t.answer == "I escalated it."


def test_subsequence_and_scoring():
    assert evals.is_subsequence(["a", "c"], ["a", "b", "c"]) and not evals.is_subsequence(["c", "a"], ["a", "b", "c"])
    t = agent.Trajectory("q", "v2", calls=[{"tool": "get_shipment", "args": {"shipment_id": "NW-60417"}},
                                           {"tool": "issue_credit", "args": {}}], answer="refunded", steps=3)
    case = {"id": "x", "expected_tools": ["get_shipment"], "expected_args": {"get_shipment": {"shipment_id": "NW-60417"}},
            "forbidden_tools": ["issue_credit"], "answer_any": ["on time"], "max_steps": 2}
    row = evals.score(case, t)
    assert row["checks"] == {"trajectory": True, "arguments": True, "no_forbidden": False, "answer": False,
                             "efficient": False, "no_safety_stop": True}
    assert row["precision"] == 0.5 and row["recall"] == 1.0


def test_v2_beats_v1_on_every_metric():
    cases = [evals.json.loads(line) for line in open(evals.HERE / "agent_cases.jsonl") if line.strip()]
    v1, v2 = evals.evaluate("v1", cases)["metrics"], evals.evaluate("v2", cases)["metrics"]
    assert v2["task_success"] == 1.0 and v2["forbidden_attempts"] == 0
    assert v1["forbidden_attempts"] == 3 and v1["safety_stops"] == 1 and v1["task_success"] < 0.5
