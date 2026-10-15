import os

os.environ.update(APP_API_KEYS="test-key", RATE_LIMIT_PER_MINUTE="3", EMBEDDER="tfidf")
from fastapi.testclient import TestClient  # noqa: E402

from app import main  # noqa: E402
from fake_llm import FakeClient, text_reply  # noqa: E402

H = {"X-API-Key": "test-key"}


def client_with(replies):
    main.state.clear()
    main.state["client"] = FakeClient(replies)
    return TestClient(main.app)


def test_ask_requires_api_key_and_returns_citations():
    with client_with([text_reply("You get 25 days [1].")]) as c:
        assert c.post("/ask", json={"question": "vacation days?"}).status_code == 401
        r = c.post("/ask", json={"question": "How many vacation days do I get?"}, headers=H)
        assert r.status_code == 200 and r.json()["sources"][0]["source"] == "vacation_policy.md"
        assert "x-request-id" in r.headers


def test_rate_limit_kicks_in():
    from app import security
    security._calls.clear()
    with client_with([text_reply("ok")] * 5) as c:
        codes = [c.post("/ask", json={"question": "hotel limit?"}, headers=H).status_code for _ in range(4)]
        assert codes == [200, 200, 200, 429]


def test_metrics_and_health():
    with client_with([]) as c:
        assert c.get("/health").json() == {"status": "ok"}
        assert c.get("/ready").json()["status"] == "ready"
        assert "ai_requests_total" in c.get("/metrics").text


def test_upload_rejects_bad_types():
    from app import security
    security._calls.clear()
    with client_with([]) as c:
        assert c.post("/documents", files={"file": ("x.exe", b"MZ", "application/octet-stream")}, headers=H).status_code == 400


def test_daily_budget_blocks_llm_calls():
    import time

    from app import security
    security._calls.clear()
    security._spend.update(day=time.strftime("%Y-%m-%d"), usd=security.DAILY_BUDGET_USD)   # pretend we spent it all
    try:
        with client_with([text_reply("never sent")]) as c:
            assert c.post("/ask", json={"question": "hotel limit?"}, headers=H).status_code == 503
    finally:
        security._spend["usd"] = 0.0


def test_llm_failure_becomes_a_clean_502():
    import anthropic

    from app import security
    security._calls.clear()

    class BrokenClient(FakeClient):
        def _create(self, **kwargs):                       # simulate Claude's API being unreachable
            raise anthropic.APIConnectionError(message="Connection error.", request=None)

    with client_with([]) as c:
        main.state["client"] = BrokenClient()
        r = c.post("/ask", json={"question": "hotel limit?"}, headers=H)
        assert r.status_code == 502 and "APIConnectionError" in r.json()["detail"]
