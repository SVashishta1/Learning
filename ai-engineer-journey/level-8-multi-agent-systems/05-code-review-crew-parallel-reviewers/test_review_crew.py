import review_crew as rc
from fake_llm import FakeClient


def test_parallel_reviewers_then_lead_merges():
    f = rc.Finding(line=9, severity="critical", title="SQL injection", why_it_matters="attackers read the DB", fix="use ? params")
    fake = FakeClient(parsed=[rc.Findings(findings=[f]), rc.Findings(findings=[]), rc.Findings(findings=[]),
                              rc.FinalReport(summary="Unsafe.", merge_recommendation="request_changes", findings=[f])])
    report, agents = rc.review("x = 1", client=fake, verbose=False)
    assert report.merge_recommendation == "request_changes" and len(agents) == 4
    lead_prompt = fake.calls[-1]["messages"][0]["content"]
    assert "SQL injection" in lead_prompt                  # the lead saw the reviewers' findings
    md = rc.to_markdown(report, "x.py")
    assert "🔴 critical" in md and "use ? params" in md


def test_numbered_lines():
    assert rc.numbered("a\nb").splitlines()[1] == "   2 | b"
