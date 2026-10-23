"""Tests (pytest -v): spans, safe logging and alerting, all offline. Spans go to an in-memory exporter."""
import json

import pytest
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

import app
import llm
import monitor
import safe_log
import telemetry
from fake_llm import FakeClaude, text_reply

MEMORY = InMemorySpanExporter()
_provider = TracerProvider()
_provider.add_span_processor(SimpleSpanProcessor(MEMORY))
trace.set_tracer_provider(_provider)          # the global provider can only be set once per process


@pytest.fixture(autouse=True)
def fresh():
    MEMORY.clear()
    yield


def spans_by_name():
    return {s.name: s for s in MEMORY.get_finished_spans()}


def test_one_question_makes_a_tree_of_spans():
    llm.set_client(FakeClaude([text_reply("It is delayed at Leeds hub.", input_tokens=90, output_tokens=12)]))
    answer = app.handle("Where is NW-58213?", "user-1")
    spans = spans_by_name()
    root = spans["handle_question"]
    assert answer.startswith("It is delayed")
    assert set(spans) == {"handle_question", "tool get_shipment", "retrieve", f"chat {llm.MODEL}"}
    for name in ("tool get_shipment", "retrieve", f"chat {llm.MODEL}"):
        assert spans[name].parent.span_id == root.context.span_id          # all children of the root
        assert spans[name].context.trace_id == root.context.trace_id       # one trace
    chat = spans[f"chat {llm.MODEL}"].attributes
    assert chat["gen_ai.usage.input_tokens"] == 90 and chat["gen_ai.request.model"] == llm.MODEL


def test_prompt_text_is_not_in_spans_by_default():
    llm.set_client(FakeClaude([text_reply("ok")]))
    app.handle("How much is Saturday delivery? my email is jo@shop.example", "user-2")
    for span in MEMORY.get_finished_spans():
        assert not any("jo@shop.example" in str(v) for v in span.attributes.values())
    assert "app.question.sha" in spans_by_name()["handle_question"].attributes


def test_handled_tool_error_is_an_event_and_model_failure_is_an_error():
    llm.set_client(FakeClaude([text_reply("Shipment not found.")]))
    app.handle("Where is NW-99999?", "user-3")
    assert "tool error" in [e.name for e in spans_by_name()["handle_question"].events]
    MEMORY.clear()

    def boom(request):
        raise RuntimeError("Overloaded")
    llm.set_client(FakeClaude(responder=boom))
    assert app.handle("How much is Saturday delivery?", "user-3").startswith("Sorry")
    root = spans_by_name()["handle_question"]
    assert root.status.status_code.name == "ERROR" and "exception" in [e.name for e in root.events]


def test_redaction_and_content_switch(monkeypatch):
    text = "Mail jo@shop.example or call 07700 900123, LS1 4AB, key sk-ant-api03-abcdefghijkl"
    assert safe_log.redact(text) == "Mail [EMAIL] or call [PHONE], [POSTCODE], key [API_KEY]"
    assert "q" not in safe_log.content_fields("q", text)                 # off by default: fingerprint only
    monkeypatch.setattr(safe_log, "LOG_CONTENT", True)
    assert safe_log.content_fields("q", text)["q"].startswith("Mail [EMAIL]")


def test_jsonl_exporter_and_monitor(tmp_path, monkeypatch):
    monkeypatch.setattr(telemetry, "TRACE_FILE", tmp_path / "traces.jsonl")
    llm.set_client(FakeClaude(responder=lambda r: text_reply("ok", input_tokens=100, output_tokens=10)))
    for _ in range(12):
        app.handle("How much is Saturday delivery?", "u")
    telemetry.JsonlSpanExporter(tmp_path / "traces.jsonl").export(MEMORY.get_finished_spans())
    stats = monitor.health(monitor.load_spans())
    assert stats["requests"] == 12 and stats["error_rate"] == 0 and stats["tokens_per_request"] == 110
    rules = json.loads(monitor.RULES_FILE.read_text())
    assert monitor.check(stats, rules) == []
    assert monitor.check(stats | {"error_rate": 0.2}, rules)[0].startswith("[PAGE] error_rate")


def test_alerts_go_to_the_webhook(monkeypatch):
    sent = []
    monkeypatch.setenv("ALERT_WEBHOOK_URL", "https://hooks.example/abc")
    import httpx
    monkeypatch.setattr(httpx, "post", lambda url, json, timeout: sent.append((url, json)))
    monitor.notify(["[PAGE] error_rate = 0.2"])
    assert sent[0][0] == "https://hooks.example/abc" and "error_rate" in sent[0][1]["text"]
