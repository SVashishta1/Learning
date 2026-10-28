"""Tests (pytest -v): token math, caches, routing, batching. Offline; the batch test drives the REAL anthropic SDK
against a fake HTTP server, so it proves our request format is accepted without spending anything."""
import json

import anthropic
import httpx2
import pytest

import batch_job
import benchmark
import cost_tools
import llm
from fake_llm import FakeClaude, json_reply, text_reply


def test_token_estimate_and_cost_math():
    assert cost_tools.estimate_tokens("x" * 400) == 100
    assert llm.cost_usd("claude-opus-5-5", 1_000_000, 0) == 4.0
    assert llm.cost_usd("claude-opus-5-5", 0, 0, cache_read=1_000_000) == pytest.approx(0.20)
    assert llm.cost_usd("claude-opus-5-5", 0, 0, cache_write=1_000_000) == pytest.approx(5.0)   # 1.25 x input


def test_monthly_cost_levers_each_save_money():
    base = cost_tools.monthly_cost(5000, 1500, 80, "claude-opus-5-5")
    cached = cost_tools.monthly_cost(5000, 1500, 80, "claude-opus-5-5", cached_tokens=1480, cache_hit_rate=0.9)
    batch = cost_tools.monthly_cost(5000, 1500, 80, "claude-opus-5-5", batch=True)
    cheap = cost_tools.monthly_cost(5000, 1500, 80, "claude-haiku-5-5")
    assert cached < base and batch == pytest.approx(base / 2) and cheap < base / 30


def test_prompt_cache_marker_is_on_the_handbook():
    fake = FakeClaude([text_reply("15:00 [handbook]")])
    llm.set_client(fake)
    cost_tools.answer("Express cut-off?")
    system = fake.calls[0]["system"][0]
    assert system["cache_control"] == {"type": "ephemeral"} and "<handbook>" in system["text"]
    assert "Express cut-off?" not in system["text"]               # the changing part stays OUT of the cached prefix


def test_response_cache_normalises_and_expires(tmp_path):
    cache = cost_tools.ResponseCache(str(tmp_path / "c.db"))
    cache.put("m", "sys", "What's the Express CUT-OFF??", "15:00")
    assert cache.get("m", "sys", "  whats the express cut-off ") == "15:00"
    assert cache.get("other-model", "sys", "whats the express cut-off") is None
    assert cache.get("m", "a different system prompt", "whats the express cut-off") is None
    cache.ttl = -1
    assert cache.get("m", "sys", "whats the express cut-off") is None


def test_router_sends_easy_to_cheap_and_hard_to_strong():
    llm.set_client(FakeClaude([json_reply({"level": "easy"}), json_reply({"level": "hard"})]))
    assert cost_tools.route("How much is Saturday delivery?")[0] == llm.CHEAP_MODEL
    assert cost_tools.route("Long complicated complaint...")[0] == llm.MODEL


def test_simulated_model_reports_cache_hits():
    sim = benchmark.SimulatedClaude()
    llm.set_client(sim)
    sim.SPEED = {"strong": (0, 0), "cheap": (0, 0)}               # no waiting in tests
    first, second = cost_tools.answer("Q1?"), cost_tools.answer("Q2?")
    assert first.cache_write_tokens > 1000 and second.cache_read_tokens == first.cache_write_tokens
    assert second.cost_usd < first.cost_usd


def test_batch_requests_are_accepted_by_the_real_sdk():
    sent = []

    def fake_api(request):
        sent.append(json.loads(request.content))
        return httpx2.Response(200, json={
            "id": "msgbatch_test", "type": "message_batch", "processing_status": "in_progress",
            "request_counts": {"processing": 200, "succeeded": 0, "errored": 0, "canceled": 0, "expired": 0},
            "created_at": "2026-10-22T00:00:00Z", "expires_at": "2026-10-23T00:00:00Z", "ended_at": None,
            "cancel_initiated_at": None, "archived_at": None, "results_url": None})
    client = anthropic.Anthropic(api_key="test", http_client=anthropic.DefaultHttpxClient(transport=httpx2.MockTransport(fake_api)))
    requests = cost_tools.batch_requests(batch_job.make_tickets(200))
    batch = client.messages.batches.create(requests=requests)
    assert batch.id == "msgbatch_test" and len(sent[0]["requests"]) == 200
    assert len({r["custom_id"] for r in requests}) == 200          # every id unique, so results can be matched
