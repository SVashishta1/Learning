"""Tests for the eval harness itself (pytest -v). Free and offline: no embedding model, no API key."""
import json

import numpy as np

import assistant
import dashboard
import llm
import metrics
import run_evals
from fake_llm import FakeClaude, json_reply, text_reply


def test_rule_metrics():
    assert metrics.exact("billing", "billing") == 1.0 and metrics.exact("billing", "other") == 0.0
    assert metrics.fact_recall("It costs £9.50 on Express", ["£9.50", "Express"]) == 1.0
    assert metrics.fact_recall("It costs £9.50", ["£9.50", "Express"]) == 0.5
    assert metrics.has_forbidden("Redirection is free", ["free"]) and not metrics.has_forbidden("freedom", ["free"])
    assert metrics.says_idk("I don't know. Please contact Northwind support.")


def test_semantic_similarity_with_a_fake_embedder():
    embed = lambda texts: np.array([[1.0, 0.0], [0.6, 0.8]])        # two unit vectors, cosine 0.6
    assert metrics.semantic_similarity("a", "b", embed) == 0.6


def test_rules_v2_passes_and_v1_regresses(tmp_path):
    good = run_evals.run("rules", "v2", use_judge=False, use_semantic=False)
    bad = run_evals.run("rules", "v1", use_judge=False, use_semantic=False)
    assert good["passed"] == good["cases"] == 20
    baseline = tmp_path / "baseline.json"
    baseline.write_text(json.dumps({"system": "rules", "version": "v2", "scores": good["scores"],
                                    "tolerance": {"default": 0.02}}))
    assert run_evals.gate(good, baseline) == []
    assert "triage_category" in run_evals.gate(bad, baseline)


def test_missing_baseline_means_no_gate(tmp_path):
    assert run_evals.gate({"scores": {"x": 0.0}}, tmp_path / "nope.json") == []


def test_llm_system_and_judge_path_with_a_fake_model():
    def responder(request):
        system = request["system"][0]["text"]
        if "grade answers" in system:                                  # the judge
            return json_reply({"critique": "Matches the reference.", "passed": True})
        if "triage" in system:
            return json_reply({"category": "late_delivery", "priority": "high"})
        return text_reply("I don't know. Please contact Northwind support.")
    llm.set_client(FakeClaude(responder=responder))
    result = run_evals.run("llm", "v2", use_judge=True, use_semantic=False)
    assert result["scores"]["answer_judge"] == 1.0
    assert result["scores"]["idk_correct"] == 0.2                     # only the 2 unanswerable cases are right
    assert result["scores"]["triage_category"] == 0.3                 # 3 of the 10 tickets are late_delivery


def test_answer_prompt_v2_contains_the_facts():
    fake = FakeClaude([text_reply("£50 per parcel.")])
    llm.set_client(fake)
    assistant.answer("How much do you pay?", "llm", "v2")
    assert "£2,500" in fake.calls[0]["system"][0]["text"]


def test_stand_in_judge_agreement_is_measured():
    llm.set_client(FakeClaude(responder=metrics.offline_judge_responder))
    result = metrics.judge_agreement(run_evals.load_jsonl("judge_calibration.jsonl"))
    assert result["n"] == 8 and result["false_pass"] == 0 and result["agreement"] >= 0.75


def test_dashboard_html_has_a_line_per_metric():
    history = [{"timestamp": "t1", "commit": "abc", "system": "rules", "version": "v1", "model": "-",
                "scores": {"a": 0.5, "b": 0.7}, "passed": 9, "cases": 20, "cost_usd": 0},
               {"timestamp": "t2", "commit": "def", "system": "rules", "version": "v2", "model": "-",
                "scores": {"a": 1.0, "b": 0.9}, "passed": 20, "cases": 20, "cost_usd": 0}]
    page = dashboard.build(history)
    assert page.count("<polyline") == 2 and "<title>Eval Dashboard</title>" in page
