"""Offline tests (pytest -v). A tiny word-hashing embedder replaces the real model so tests are fast and free."""
import zlib

import numpy as np
import pytest

import llm
import rag
from fake_llm import FakeClaude, json_reply


class WordEmbedder(rag.Embedder):
    """Fake 'meaning' vectors: one slot per (hashed) word. Similar words in common -> similar vectors."""
    def __init__(self):
        super().__init__("test")

    def encode(self, texts):
        v = np.zeros((len(texts), 256))
        for row, text in enumerate(texts):
            for word in rag.tokenize(text):
                v[row, zlib.crc32(word.encode()) % 256] += 1
        return v / (np.linalg.norm(v, axis=1, keepdims=True) + 1e-12)


@pytest.fixture(scope="module")
def index():
    return rag.Index.from_folder(embedder=WordEmbedder())


def test_tokenizer_keeps_codes_and_stems_words():
    assert rag.tokenize("Form CL-7, UN3481 and £6 at 15:00") == ["form", "cl-7", "un3481", "£6", "15:00"]
    assert rag.stem("redirection") == rag.stem("redirect") == "redirect"
    assert rag.stem("batteries") == "battery"


def test_heading_chunks_keep_their_heading_path():
    chunks = rag.chunk_by_heading("x.md", "# Title\n\n## Part A\nOne.\n\n## Part B\nTwo.")
    assert chunks == [("Title > Part A", "One."), ("Title > Part B", "Two.")]
    fixed = rag.chunk_fixed("x.md", "# Title\n\n## Part A\nOne.\n\n## Part B\nTwo.")
    assert all("Part" not in text for _, text in fixed)               # blind chunks lose the headings


def test_bm25_prefers_rare_matching_words():
    bm = rag.BM25([["parcel", "late"], ["parcel", "un3481"], ["parcel"]])
    s = bm.scores(["parcel", "un3481"])
    assert s.argmax() == 1 and s[1] > 5 * s[0]          # "parcel" is in every chunk, so it counts for little
    assert s[2] > s[0]                                  # same match, shorter chunk -> slightly higher score


def test_rrf_rewards_agreement():
    fused = rag.rrf([[1, 2, 3], [2, 1, 4]])
    assert fused[1] == fused[2] == pytest.approx(1 / 61 + 1 / 62)
    assert fused[3] == pytest.approx(1 / 63) and fused[4] == pytest.approx(1 / 63)


def test_hybrid_search_finds_codes(index):
    hits = index.search("Can I send UN3481 batteries?", k=3)
    assert hits[0].chunk.doc == "dangerous-goods.md" and "UN3481" in hits[0].chunk.text
    assert hits[0].ranks["keyword"] == 1


def test_gate_says_i_dont_know_without_calling_the_model(index):
    fake = FakeClaude()
    llm.set_client(fake)
    result = index and rag.answer(index, "pancake recipe with syrup")
    assert result["found"] is False and result["stopped_by"] == "retrieval gate"
    assert fake.calls == []                                           # no tokens spent


def test_cited_answer(index):
    fake = FakeClaude([json_reply({"found": True, "answer": "Yes, by road, with the battery mark [1].", "citations": [1]})])
    llm.set_client(fake)
    result = rag.answer(index, "Can I send UN3481 batteries?")
    assert result["found"] and result["sources"][0]["label"].startswith("dangerous-goods.md")
    prompt = fake.calls[0]["messages"][0]["content"]
    assert '<source n="1"' in prompt and "<question>" in prompt
    assert fake.calls[0]["output_config"]["format"]["type"] == "json_schema"


def test_checks_catch_invented_citations_and_numbers(index):
    hits = index.search("Can I send UN3481 batteries?", k=2)
    bad = rag.Answer(found=True, answer="Yes, it costs £99 [1] and is fine [7].", citations=[1, 7])
    problems = rag.check_answer(bad, hits)
    assert any("[7]" in p for p in problems) and any("£99" in p for p in problems)


def test_model_not_found_becomes_i_dont_know(index):
    llm.set_client(FakeClaude([json_reply({"found": False, "answer": "Not in the sources.", "citations": []})]))
    result = rag.answer(index, "Do you deliver parcels to France?")
    assert result["found"] is False and result["answer"] == rag.IDK


def test_llm_reranker_reorders_by_rating(index):
    hits = index.search("Can I send UN3481 batteries?", k=3)
    llm.set_client(FakeClaude([json_reply({"scores": [{"n": 1, "relevance": 1}, {"n": 2, "relevance": 3}, {"n": 3, "relevance": 0}]})]))
    reranked = rag.rerank_llm("Can I send UN3481 batteries?", hits)
    assert reranked[0].chunk.id == hits[1].chunk.id and reranked[0].ranks["rerank"] == 3


def test_offline_stand_in_answers_from_the_sources(index):
    llm.set_client(FakeClaude(responder=rag.offline_responder))
    result = rag.answer(index, "Can I send UN3481 batteries?")
    assert result["found"] and "UN3481" in result["answer"] and result["problems"] == []
