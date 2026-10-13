from fake_llm import FakeClient, text_reply
from rag import Embedder, Index, answer, chunk_text

index = Index(Embedder("tfidf")).build("docs")      # keyword embedder: works offline in CI


def test_chunks_respect_size_and_overlap():
    text = " ".join(f"Sentence number {i} is here." for i in range(100))
    chunks = chunk_text(text, size=200, overlap=40)
    assert all(len(c) <= 260 for c in chunks) and len(chunks) > 5
    assert chunks[0][-20:].strip() in chunks[1]        # overlap carried forward


def test_retrieval_finds_the_right_document():
    assert index.search("How much can I spend on meals when travelling?")[0][0].source == "expense_policy.md"
    assert index.search("minimum password length")[0][0].source == "it_security.md"
    assert index.search("parental leave weeks")[0][0].source == "vacation_policy.md"


def test_answer_sends_sources_and_parses_citations():
    fake = FakeClient([text_reply("You can carry over up to 5 days [1].")])
    result = answer(fake, index, "How many vacation days can I carry over?")
    prompt = fake.calls[0]["messages"][0]["content"]
    assert "<sources>" in prompt and "[1]" in prompt
    assert result["sources"][0]["source"] == "vacation_policy.md"
