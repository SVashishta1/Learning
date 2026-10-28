"""Tests (pytest -v): durability, retries, approvals and idempotency. Offline, fast, each test in its own folder."""
import pytest

import llm
import services
import workflow
from fake_llm import FakeClaude, json_reply


@pytest.fixture
def store(tmp_path, monkeypatch):
    monkeypatch.setattr(services, "DB", tmp_path / "services.db")
    monkeypatch.setattr(workflow, "BASE_DELAY", 0)                    # no waiting in tests
    llm.set_client(FakeClaude(responder=workflow.offline_responder))
    s = workflow.Store(tmp_path / "workflow.db")
    s.start_run("t", workflow.LATE_SHIPMENTS)
    return s


def credits():
    return services._db().execute("SELECT customer, amount_gbp FROM credits").fetchall()


def test_credit_policy_is_code():
    ship = services.get_shipment("NW-61502")                          # gold, Express, 3 days late
    assert workflow.decide_credit(ship) == {"amount_gbp": 19.5, "needs_approval": True, "reasons": [
        "Express surcharge refund (£4.50)", "£15 goodwill credit for a gold customer"]}
    assert workflow.decide_credit(services.get_shipment("NW-61655"))["amount_gbp"] == 0      # Standard, 1 day late


def test_run_parks_for_approval_then_finishes(store):
    result = workflow.advance(store, "t", fail_rate=0, verbose=False)
    assert result == {"complete": 4, "waiting_approval": 1, "failed": 1, "rejected": 0, "in_progress": 0}
    assert ("Harbour Fresh Foods", 19.5) not in credits()            # nothing paid before the human says yes
    store.db.execute("UPDATE approvals SET status='approved', decided_by='alice' WHERE id=1")
    store.db.commit()
    assert workflow.advance(store, "t", fail_rate=0, verbose=False)["complete"] == 5
    assert ("Harbour Fresh Foods", 19.5) in credits()


def test_rejection_stops_the_item(store):
    workflow.advance(store, "t", fail_rate=0, verbose=False)
    store.db.execute("UPDATE approvals SET status='rejected', decided_by='bob' WHERE id=1")
    store.db.commit()
    assert workflow.advance(store, "t", fail_rate=0, verbose=False)["rejected"] == 1
    assert store.get("t", "NW-61502", "send_email")["status"] == "pending"


def test_resume_after_crash_does_not_redo_finished_steps(store, monkeypatch):
    with pytest.raises(workflow.Crash):
        workflow.advance(store, "t", fail_rate=0, crash_after=7, verbose=False)
    fetched = []
    real = services.get_shipment
    monkeypatch.setattr(services, "get_shipment", lambda sid, rate=0: fetched.append(sid) or real(sid, rate))
    workflow.advance(store, "t", fail_rate=0, verbose=False)
    assert "NW-61204" not in fetched and "NW-61377" not in fetched   # finished before the crash: not fetched again


def test_crash_inside_a_side_effect_is_safe_because_of_idempotency(store):
    with pytest.raises(workflow.Crash):
        workflow.advance(store, "t", fail_rate=0, crash_in="issue_credit", verbose=False)
    assert credits() == [("Kestrel Pharmacy", 4.5)]                  # the credit WAS issued before the crash
    assert store.get("t", "NW-61204", "issue_credit")["status"] == "running"
    workflow.advance(store, "t", fail_rate=0, verbose=False)
    assert credits().count(("Kestrel Pharmacy", 4.5)) == 1            # ...and not issued twice on resume
    assert store.get("t", "NW-61204", "issue_credit")["result"]["replayed"] is True


def test_transient_errors_are_retried_then_given_up(store):
    result = workflow.advance(store, "t", fail_rate=1.0, verbose=False)   # the shipments API is always down
    first = store.get("t", "NW-61204", "fetch_shipment")
    assert first["status"] == "failed" and first["attempts"] == workflow.MAX_ATTEMPTS
    assert result["failed"] == 6 and credits() == []                     # nothing half-done


def test_permanent_error_is_tried_once(store):
    workflow.advance(store, "t", fail_rate=0, verbose=False)
    state = store.get("t", "NW-69999", "fetch_shipment")
    assert state["status"] == "failed" and state["attempts"] == 1 and "404" in state["error"]


def test_bad_draft_is_retried(store):
    replies = [json_reply({"subject": "Sorry", "body": "Sorry it was late."}),                    # forgot the amount
               json_reply({"subject": "Sorry", "body": "Sorry. We added a credit of £4.50."})]
    llm.set_client(FakeClaude(replies))
    ship = services.get_shipment("NW-61204")
    with pytest.raises(services.TransientError):
        workflow.draft_email(ship, workflow.decide_credit(ship))
    assert "£4.50" in workflow.draft_email(ship, workflow.decide_credit(ship))["body"]
