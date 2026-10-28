"""Lesson 20: provider selection, secrets from files, the preflight checks and the app. No cloud account needed."""
from types import SimpleNamespace as NS

import anthropic
import pytest
from fastapi.testclient import TestClient

import app as app_module
import preflight
import providers


@pytest.fixture(autouse=True)
def clean_env(monkeypatch, tmp_path):
    for var in ("LLM_PROVIDER", "ANTHROPIC_API_KEY", "BEDROCK_BASE_URL", "PRIVATE_ONLY", "EXPECT_NO_INTERNET", "APP_URL"):
        monkeypatch.delenv(var, raising=False)
    monkeypatch.setenv("SECRETS_DIR", str(tmp_path))
    app_module._brain = None


def test_secret_file_wins_over_env(monkeypatch, tmp_path):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "from-env")
    assert providers.read_secret("ANTHROPIC_API_KEY") == "from-env"
    (tmp_path / "anthropic_api_key").write_text("from-file\n")
    assert providers.read_secret("ANTHROPIC_API_KEY") == "from-file"


def test_bedrock_uses_iam_and_an_optional_private_endpoint(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "bedrock")
    monkeypatch.setenv("AWS_REGION", "eu-central-1")
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "AKIAFAKE")              # stands in for the VM's role credentials
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "fake")
    b = providers.get_brain()
    assert isinstance(b.client, anthropic.AnthropicBedrockMantle) and b.model == "anthropic.claude-opus-5-5"
    assert str(b.client.base_url) == "https://bedrock-mantle.eu-central-1.api.aws/anthropic/"
    monkeypatch.setenv("BEDROCK_BASE_URL", "https://vpce-0abc.bedrock-mantle.eu-central-1.vpce.amazonaws.com/anthropic")
    assert "vpce-0abc" in str(providers.get_brain().client.base_url)


def test_vertex_client(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "vertex")
    monkeypatch.setenv("GCP_PROJECT", "northwind-ai")
    monkeypatch.setenv("GCP_REGION", "europe-west1")
    monkeypatch.setattr(anthropic, "AnthropicVertex", lambda **kw: NS(kw=kw))   # no Google credentials in tests
    b = providers.get_brain()
    assert b.client.kw == {"project_id": "northwind-ai", "region": "europe-west1"} and b.model == "claude-opus-5-5"


def test_anthropic_needs_a_secret(monkeypatch, tmp_path):
    monkeypatch.setenv("LLM_PROVIDER", "anthropic")
    with pytest.raises(RuntimeError, match="No ANTHROPIC_API_KEY"):
        providers.get_brain()
    (tmp_path / "anthropic_api_key").write_text("sk-ant-test")
    assert providers.get_brain().model == "claude-opus-5-5"


def test_ask_with_a_stub_claude_client():
    reply = NS(stop_reason="end_turn", content=[NS(type="text", text="It is in Rotterdam.")])
    sent = {}
    client = NS(messages=NS(create=lambda **kw: sent.update(kw) or reply))
    assert providers.Brain("bedrock", client, "anthropic.claude-opus-5-5").ask("Where is NW-1234567?") == "It is in Rotterdam."
    assert sent["model"] == "anthropic.claude-opus-5-5" and sent["output_config"] == {"effort": "low"}


def test_preflight_flags_a_public_model_endpoint(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "bedrock")
    monkeypatch.setenv("AWS_REGION", "eu-central-1")
    monkeypatch.setenv("PRIVATE_ONLY", "1")
    monkeypatch.setenv("EXPECT_NO_INTERNET", "1")
    monkeypatch.setattr(preflight, "resolve", lambda host: ["52.28.1.10"])          # a public address
    monkeypatch.setattr(preflight, "can_connect", lambda host, port, timeout=3.0: False)
    rows = {name: status for name, status, _ in preflight.run_checks()}
    assert rows["dns: model endpoint is private"] == "FAIL" and rows["egress: internet blocked"] == "PASS"
    monkeypatch.setattr(preflight, "resolve", lambda host: ["10.42.0.17", "10.42.1.23"])   # VPC endpoint IPs
    rows = {name: status for name, status, _ in preflight.run_checks()}
    assert rows["dns: model endpoint"] == "PASS"


def test_app_ready_and_ask_in_fake_mode(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "fake")
    c = TestClient(app_module.app)
    assert c.get("/healthz").json() == {"ok": True}
    assert c.get("/ready").json()["provider"] == "fake"
    assert c.post("/ask", json={"question": "Where is NW-1234567?"}).json()["answer"].startswith("(FAKE)")
    assert c.post("/ask", json={"question": "x"}).status_code == 422


def test_app_not_ready_without_secret(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "anthropic")
    r = TestClient(app_module.app).get("/ready")
    assert r.status_code == 503 and "ANTHROPIC_API_KEY" in r.json()["detail"]
