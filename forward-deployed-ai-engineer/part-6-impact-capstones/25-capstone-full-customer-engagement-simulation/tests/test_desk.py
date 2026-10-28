"""End to end in FAKE mode: team, approvals with the supervisor rule, execution through the API, evals, web app."""
import time

import pytest
from fastapi.testclient import TestClient

import mock_api
from app import app
from evals.run_evals import run
from team import decide, run_desk


@pytest.fixture(autouse=True)
def fresh_mock():
    mock_api.reset()


def test_desk_queues_everything_and_supervisor_rule_holds():
    m = run_desk()
    assert m.status == "awaiting_approval"
    credit_1850 = next(a for a in m.actions if a.kind == "credit" and a.args["amount_eur"] == 1850)
    with pytest.raises(PermissionError):
        decide(m, credit_1850.id, True, "Priya", "handler")
    decide(m, credit_1850.id, True, "Joanna", "supervisor")
    reply = next(a for a in m.actions if a.kind == "customer_reply" and a.args["ticket_id"] == "T-1002")
    decide(m, reply.id, True, "Priya", "handler")
    m.execute_approved()
    assert mock_api.OUTBOX["credits"] == [{"ticket_id": "T-1002", "tracking": "NW-4821901", "amount_eur": 1850.0,
                                           "approved_by": "Joanna (supervisor)"}]
    assert mock_api.OUTBOX["replies"][0]["text"].startswith("Beste klant")
    assert len(mock_api.OUTBOX["notes"]) == 7                       # internal notes need no approval


def test_golden_set():
    for row in run():
        assert all(row["checks"].values()), (row["id"], [k for k, v in row["checks"].items() if not v])


def test_web_app():
    c = TestClient(app)
    assert "claims desk" in c.get("/").text
    rid = c.post("/api/runs").json()["id"]
    for _ in range(80):
        r = c.get(f"/api/runs/{rid}").json()
        if r["status"] not in ("created", "running"):
            break
        time.sleep(0.1)
    assert r["status"] == "awaiting_approval" and len(r["claims"]) == 7
    big = next(a for a in r["actions"] if a["args"].get("needs_supervisor"))
    assert c.post(f"/api/runs/{rid}/actions/{big['id']}", json={"approve": True, "by": "Priya"}).status_code == 403
    assert c.post(f"/api/runs/{rid}/actions/{big['id']}", json={"approve": True, "by": "Joanna", "role": "supervisor"}).status_code == 200
    assert c.post(f"/api/runs/{rid}/execute").json()[0]["status"] == "executed"
    assert c.get("/api/outbox").json()["credits"][0]["amount_eur"] == 1850
