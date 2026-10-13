import writer_critic as wc
from fake_llm import FakeClient, text_reply


def test_loop_stops_when_score_reaches_target():
    wc.WRITER.client = FakeClient([text_reply("draft one"), text_reply("draft two")])
    wc.CRITIC.client = FakeClient(parsed=[wc.Critique(score=5, strengths=[], fixes=["be specific"], ready=False),
                                          wc.Critique(score=9, strengths=["clear"], fixes=[], ready=True)])
    wc.WRITER.verbose = wc.CRITIC.verbose = False
    final, history = wc.write_with_feedback("a haiku")
    assert final == "draft two" and [h["score"] for h in history] == [5, 9]
    assert "be specific" in wc.WRITER.client.calls[1]["messages"][0]["content"]   # feedback reached the writer
