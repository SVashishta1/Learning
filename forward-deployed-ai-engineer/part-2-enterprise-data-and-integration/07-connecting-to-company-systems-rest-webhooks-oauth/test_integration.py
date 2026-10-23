import json

import pytest
from fastapi.testclient import TestClient

import mock_systems as mock
import signing
import webhook_receiver as receiver
from company_client import APIError, CompanyClient


@pytest.fixture
def clock(monkeypatch):
    """A fake clock shared by the mock server and the client: sleeping moves time forward instantly."""
    t = [1_800_000_000.0]
    monkeypatch.setattr(mock, "now", lambda: t[0])
    for store in (mock.TOKENS, mock.CALLS, mock.NOTES, mock.IDEMPOTENCY):
        store.clear()
    monkeypatch.setattr(mock, "FAIL_RATE", 0.0)
    return t


def make_client(clock, client_id="fde-assistant", secret="assistant-secret-change-me", **kwargs):
    logs = []
    client = CompanyClient("http://testserver", client_id, secret, http=TestClient(mock.app),
                           sleep=lambda s: clock.__setitem__(0, clock[0] + s), clock=lambda: clock[0],
                           log=logs.append, **kwargs)
    return client, logs


def test_token_endpoint_checks_client_grant_and_scope(clock):
    api = TestClient(mock.app)
    form = {"grant_type": "client_credentials"}
    assert api.post("/oauth/token", data=form, auth=("fde-assistant", "nope")).status_code == 401
    assert api.post("/oauth/token", data={"grant_type": "password"}, auth=("fde-assistant", "x")).status_code == 400
    bad_scope = api.post("/oauth/token", data={**form, "scope": "tickets.write"},
                         auth=("readonly-bot", "readonly-secret-change-me"))
    assert bad_scope.json() == {"error": "invalid_scope"}
    ok = api.post("/oauth/token", data={**form, "scope": "crm.read"}, auth=("readonly-bot", "readonly-secret-change-me"))
    assert ok.json()["scope"] == "crm.read" and ok.json()["token_type"] == "Bearer"


def test_requests_need_a_token_and_the_right_scope(clock):
    assert TestClient(mock.app).get("/crm/accounts").status_code == 401
    client, _ = make_client(clock, "readonly-bot", "readonly-secret-change-me")
    with pytest.raises(APIError, match="403"):
        client.add_note(1, "should not be allowed")


def test_both_pagination_styles_return_everything(clock):
    client, _ = make_client(clock)
    accounts = list(client.iter_accounts(page_size=20))
    assert len(accounts) == 45 and len({a["id"] for a in accounts}) == 45
    assert len(list(client.iter_tickets())) == 112
    assert len(list(client.iter_tickets(status="open"))) == 75


def test_rate_limit_is_respected_with_retry_after(clock, monkeypatch):
    monkeypatch.setattr(mock, "RATE_LIMIT", 2)
    client, logs = make_client(clock)
    accounts = list(client.iter_accounts(page_size=5))              # 9 pages, only 2 allowed per second
    assert len(accounts) == 45
    assert any("HTTP 429, waiting 1.00 s" in line for line in logs)


def test_random_server_errors_are_retried(clock, monkeypatch):
    monkeypatch.setattr(mock, "FAIL_RATE", 0.4)
    client, logs = make_client(clock)
    assert len(list(client.iter_tickets())) == 112
    assert client.stats["retries"] > 0 and any("HTTP 503" in line for line in logs)


def test_gives_up_after_max_retries(clock, monkeypatch):
    monkeypatch.setattr(mock, "FAIL_RATE", 1.0)
    client, _ = make_client(clock, max_retries=3)
    with pytest.raises(APIError, match="503"):
        list(client.iter_accounts())
    assert client.stats["retries"] == 3


def test_token_is_reused_then_refreshed_before_expiry(clock):
    client, _ = make_client(clock)
    list(client.iter_accounts())
    assert client.stats["tokens"] == 1                              # 3 pages, 1 token
    clock[0] += mock.TOKEN_TTL - 10                                 # 10 s before expiry: inside the 30 s margin
    list(client.iter_accounts())
    assert client.stats["tokens"] == 2


def test_revoked_token_is_replaced_once(clock):
    client, _ = make_client(clock)
    client.token()
    mock.TOKENS.clear()                                             # the server forgets every token
    assert len(list(client.iter_accounts())) == 45


def test_idempotency_key_prevents_duplicate_notes(clock):
    client, _ = make_client(clock)
    first = client.add_note(3, "Draft ready", idempotency_key="key-1")
    again = client.add_note(3, "Draft ready", idempotency_key="key-1")
    other = client.add_note(3, "Second note")
    assert first == again and other["id"] != first["id"]
    assert len(mock.NOTES[3]) == 2


def test_signature_round_trip_and_attacks():
    body = b'{"id": "evt_1"}'
    header = signing.sign("s3cret", body, timestamp=1000)
    assert signing.verify("s3cret", header, body, now=1010)
    for bad_body, bad_header, now, reason in [
        (b'{"id": "evt_2"}', header, 1010, "does not match"),           # tampered body
        (body, signing.sign("guess", body, 1000), 1010, "does not match"),  # wrong secret
        (body, header, 1000 + 301, "too old"),                          # replay
        (body, None, 1010, "missing"),
        (body, "garbage", 1010, "malformed"),
    ]:
        with pytest.raises(ValueError, match=reason):
            signing.verify("s3cret", bad_header, bad_body, now=now)


def test_mock_helpdesk_delivers_signed_webhooks_to_the_receiver(clock, monkeypatch):
    clock[0] = __import__("time").time()                           # the receiver checks against real time
    receiver.PROCESSED.clear()
    receiver.RECEIVED.clear()
    monkeypatch.setattr(mock, "webhook_http", TestClient(receiver.app))
    result = TestClient(mock.app).post("/admin/simulate/ticket-created",
                                       params={"target": "/webhooks/helpdesk", "ticket_id": 7, "times": 2}).json()
    assert result["delivered_status_codes"] == [200, 200]
    assert len(receiver.RECEIVED) == 1                              # delivered twice, processed once
    assert receiver.RECEIVED[0]["data"]["id"] == 7


def test_receiver_rejects_unsigned_and_tampered():
    api = TestClient(receiver.app)
    body = json.dumps({"id": "evt_x", "type": "ticket.created", "data": {"id": 1, "subject": "x"}}).encode()
    assert api.post("/webhooks/helpdesk", content=body).status_code == 401
    header = signing.sign(receiver.WEBHOOK_SECRET, body)
    tampered = body.replace(b'"x"', b'"refund"')
    assert api.post("/webhooks/helpdesk", content=tampered, headers={signing.HEADER: header}).status_code == 401
