import research_team as rt
from fake_llm import FakeClient, text_reply


class RoutingFake(FakeClient):
    """Answers depend on WHO is asking (threads make call order unpredictable)."""
    def _create(self, **kw):
        self.calls.append(kw)
        system = kw["system"]
        if "researcher" in system:
            return text_reply(f"- fact about {kw['messages'][0]['content'][:20]} (https://example.com)")
        return text_reply("Report with citations [1].")


def test_full_pipeline_with_parallel_researchers():
    fake = RoutingFake(parsed=[rt.Plan(sub_questions=["q one", "q two", "q three"], audience="students"),
                               rt.FactCheck(unsupported_claims=[], missing_citations=[], verdict="pass")])
    report, agents = rt.run("topic", client=fake, verbose=False)
    assert report == "Report with citations [1]."
    researcher_calls = [c for c in fake.calls if "researcher" in c["system"]]
    assert len(researcher_calls) == 3
    assert researcher_calls[0]["tools"][0]["type"] == "web_search_20260209"
    writer_prompt = [c for c in fake.calls if "research briefs" in c["system"]][0]["messages"][0]["content"]
    assert "q two" in writer_prompt
