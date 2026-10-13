from evaluate import CASES, Verdict, judge, retrieval_metrics
from fake_llm import FakeClient
from rag import Embedder, Index


def test_retrieval_metrics_are_reasonable_offline():
    index = Index(Embedder("tfidf")).build("docs")
    m = retrieval_metrics(index, k=3)
    assert 0.8 <= m["hit_rate"] <= 1.0 and 0 < m["mrr"] <= 1


def test_judge_gets_question_answer_and_sources():
    fake = FakeClient(parsed=[Verdict(correct=True, faithful=True, reason="matches source")])
    result = {"answer": "25 days [1].", "sources": [{"n": 1, "text": "Full-time employees receive 25 days"}]}
    verdict = judge(fake, CASES[0], result)
    assert verdict.correct
    prompt = fake.calls[0]["messages"][0]["content"]
    assert "25 days [1]." in prompt and "Full-time employees" in prompt
