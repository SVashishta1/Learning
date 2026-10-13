import company_data as db
import support_team as st
from fake_llm import FakeClient, text_reply, tool_reply


def quiet():
    for a in [st.ROUTER, *st.SPECIALISTS.values()]:
        a.verbose = False
        a.approver = lambda *args: True


def test_refund_policy_is_enforced_in_code():
    assert "Refunded $29.0" in st.issue_refund("INV-502", "duplicate")
    assert "manager" in st.issue_refund("INV-701", "seats")          # $249 > $50 limit -> human review
    assert db.INVOICES["INV-701"]["status"] == "paid"


def test_router_sends_to_specialist_and_handoff_works():
    quiet()
    st.ROUTER.client = FakeClient(parsed=[st.Triage(category="technical", urgency="normal", sentiment="calm", summary="wants refund")])
    st.SPECIALISTS["technical"].client = FakeClient([tool_reply("handoff", {"to": "billing", "note": "refund request"}),
                                                     text_reply("A billing colleague will help.")])
    st.SPECIALISTS["billing"].client = FakeClient([text_reply("Refund done.")])
    reply = st.handle("C-1001", "refund please")
    assert "billing colleague" in reply and "Refund done." in reply
    assert "refund request" in st.SPECIALISTS["billing"].client.calls[0]["messages"][0]["content"]
