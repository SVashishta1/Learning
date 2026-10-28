"""Tests (pytest -v): tools, budgets, step limits and the whole team run, offline with scripted models."""
import json

import pytest

import llm
import make_data
import offline_brain
import team
import tools
from fake_llm import FakeClaude, tool_reply


@pytest.fixture(autouse=True)
def database(tmp_path_factory, monkeypatch):
    db = tmp_path_factory.getbasetemp() / "northwind.db"
    if not db.exists():
        monkeypatch.setattr(make_data, "DB", db)
        make_data.main()
    monkeypatch.setattr(tools, "DB", db)
    llm.set_client(FakeClaude(responder=offline_brain.respond))


def test_sql_tool_is_read_only_and_single_statement():
    assert "only a single SELECT" in tools.run_sql("DELETE FROM shipments")
    assert "only a single SELECT" in tools.run_sql("SELECT 1; DROP TABLE shipments")
    rows = json.loads(tools.run_sql("SELECT COUNT(*) AS n FROM shipments"))
    assert rows == [{"n": 1720}]
    assert "ERROR" in tools.run_sql("SELECT nope FROM shipments")


def test_contract_maths_is_done_by_code():
    assert json.loads(tools.calculate_service_credit(92.5, 10000)) == {"points_below_95": 2, "credit_rate": 0.1, "credit_gbp": 1000.0}
    assert json.loads(tools.calculate_service_credit(54.0, 48000))["credit_gbp"] == 12000.0      # capped at 25%


def test_each_specialist_only_has_its_own_tools():
    names = {role: {d["name"] for d, _ in toolset} for role, toolset in tools.TOOLSETS.items()}
    assert names["contracts"] == {"search_documents", "calculate_service_credit"}
    assert "run_sql" not in names["customer_voice"] | names["operations"] | names["contracts"]


def test_budget_stops_the_team():
    budget = team.Budget(max_usd=10, max_calls=1)
    budget.check("x")
    budget.calls = 1
    with pytest.raises(team.BudgetExceeded):
        budget.check("x")
    report = team.Specialist("operations", None).run(
        team.Task(task_id="T1", specialist="operations", question="What happened?"), budget)
    assert report.status == "partial" and "Budget ran out" in report.open_questions[0]


def test_step_limit_gives_a_partial_report():
    calls = []

    def looping(request):                              # a model that never stops calling tools
        calls.append(1)
        if "format" in request.get("output_config", {}):
            return offline_brain.json_reply({"status": "complete", "summary": "s", "findings": [],
                                             "recommendations": [], "open_questions": []})
        return tool_reply("ticket_stats", {"month": "2026-09"}, call_id=f"c{len(calls)}")
    llm.set_client(FakeClaude(responder=looping))
    report = team.Specialist("customer_voice", None, max_steps=3).run(
        team.Task(task_id="T1", specialist="customer_voice", question="?"), team.Budget())
    assert report.status == "partial" and len(calls) == 4          # 3 tool rounds + 1 report call


def test_specialists_receive_the_task_as_json():
    fake = FakeClaude(responder=offline_brain.respond)
    llm.set_client(fake)
    team.Specialist("contracts", "claude-haiku-5-5").run(
        team.Task(task_id="T4", specialist="contracts", question="What do contracts say?"), team.Budget())
    first = json.loads(fake.calls[0]["messages"][0]["content"])
    assert first["task_id"] == "T4" and fake.calls[0]["model"] == "claude-haiku-5-5"


def test_whole_team_offline():
    budget = team.Budget()
    head = team.Head(budget, model="claude-opus-5-5", cheap_model="claude-haiku-5-5")
    final = head.run(team.QUESTION)
    assert {t[0] for t in head.reports} == {"T", "F"} and len(head.reports) == 6      # 4 tasks + 2 follow-ups
    assert "63 of 124" in final.root_causes[0].share_of_late_shipments
    assert any("£12,000" in a.action and a.needs_human_approval for a in final.actions)
    assert budget.by_agent["operations"]["model"] == "claude-haiku-5-5"
    markdown = team.to_markdown(team.QUESTION, final, budget)
    assert "[NEEDS YOUR APPROVAL]" in markdown and "| Cause |" in markdown
