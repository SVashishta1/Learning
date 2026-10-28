"""The policy rules, the policy search and the integration client."""
import pytest

import mock_api
from claims_tools import PolicyIndex, assess
from northwind_client import NorthwindClient


@pytest.fixture(autouse=True)
def fresh_mock():
    mock_api.reset()
    yield
    mock_api.FAIL_RATE = 0.0


def claim(**kw):
    base = {"claim_id": "C-1", "tracking": "NW-4821736", "claim_type": "damage", "claimed_eur": 640.0,
            "has_photos": True, "received": "2026-10-20T09:00"}
    return {**base, **kw}


def ship(**kw):
    base = {"weight_kg": 380, "declared_value_eur": 4200, "insured": False, "service": "standard",
            "shipping_fee_eur": 310, "expected_delivery": "2026-10-19", "delivered_at": "2026-10-19T14:10",
            "pod_remark": "pallet damaged"}
    return {**base, **kw}


def test_damage_within_limit_is_paid_in_full():
    assert assess(claim(), ship())["outcome"] == "approve_full"


def test_uninsured_cap_is_ten_euro_per_kg():
    r = assess(claim(claimed_eur=25000), ship(weight_kg=5, declared_value_eur=120))
    assert (r["outcome"], r["amount_eur"]) == ("approve_partial", 50)


def test_clean_pod_and_late_report_is_rejected_but_noted_pod_allows_30_days():
    late = claim(received="2026-10-30T09:00")
    assert assess(late, ship(pod_remark="signed clean"))["outcome"] == "reject"
    assert assess(late, ship(pod_remark="box dented"))["outcome"] == "approve_full"


def test_no_photos_means_ask_first():
    assert assess(claim(has_photos=False), ship())["outcome"] == "need_info"


def test_loss_insured_above_handler_limit_needs_supervisor():
    r = assess(claim(claim_type="loss", claimed_eur=1850, received="2026-10-21T13:40"),
               ship(insured=True, declared_value_eur=1850, delivered_at=None, expected_delivery="2026-10-02"))
    assert (r["outcome"], r["amount_eur"], r["needs_supervisor"]) == ("approve_full", 1850, True)


def test_delay_refund_only_for_express_over_48h():
    late = ship(service="express", shipping_fee_eur=95, expected_delivery="2026-10-14", delivered_at="2026-10-17T11:00")
    assert assess(claim(claim_type="delay", claimed_eur=None), late)["amount_eur"] == 95
    assert assess(claim(claim_type="delay", claimed_eur=None), {**late, "service": "standard"})["outcome"] == "reject"


def test_unknown_shipment():
    assert assess(claim(tracking="NW-0000000"), None)["outcome"] == "need_info"


def test_policy_search_finds_delay_rules():
    assert PolicyIndex().search("express shipment delivered late fee refund")[0]["chunk_id"] == "claims-policy#delay-compensation"


def test_client_gets_a_token_and_retries_a_busy_tms():
    mock_api.FAIL_RATE = 0.5
    c = NorthwindClient()
    assert c.shipment("NW-4822010")["service"] == "express"          # succeeds despite 503s
    with pytest.raises(KeyError):
        c.shipment("NW-0000000")


def test_wrong_secret_is_refused(monkeypatch):
    monkeypatch.setenv("MOCK_CLIENT_SECRET", "wrong")
    with pytest.raises(Exception, match="401"):
        NorthwindClient().new_claims()
