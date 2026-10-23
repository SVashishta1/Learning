"""compare_retrieval.py: measure which retrieval setup finds the right chunk most often. Free and offline.

python compare_retrieval.py                  # 2 chunkers x 3 search modes, plus the "I don't know" calibration
python compare_retrieval.py --rerank llm     # also score hybrid + reranking (needs a model; or add --offline)
"""
import argparse
import json
from pathlib import Path

import llm
import rag

CASES = [json.loads(line) for line in Path(__file__).with_name("questions.jsonl").open(encoding="utf-8")]


def is_hit(case: dict, hit: rag.Hit) -> bool:
    """Right document AND the chunk really contains the key fact."""
    return hit.chunk.doc == case["doc"] and case["must_include"].lower() in hit.chunk.text.lower()


def score(index: rag.Index, mode: str, rerank=None, k: int = 4) -> dict:
    answerable = [c for c in CASES if not c.get("unanswerable")]
    hit1 = hitk = rr = 0.0
    misses = []
    for case in answerable:
        found = [is_hit(case, h) for h in index.search(case["question"], k, mode=mode, rerank=rerank)]
        hit1 += found[0] if found else 0
        hitk += any(found)
        rr += 1 / (found.index(True) + 1) if any(found) else 0     # reciprocal rank: 1st = 1, 2nd = 0.5 ...
        if not any(found):
            misses.append(case["question"][:45])
    n = len(answerable)
    return {"hit@1": hit1 / n, f"hit@{k}": hitk / n, "mrr": rr / n, "misses": misses}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--rerank", choices=["llm", "cross-encoder"])
    parser.add_argument("--offline", action="store_true")
    args = parser.parse_args()
    if args.offline:
        from fake_llm import FakeClaude
        llm.set_client(FakeClaude(responder=rag.offline_responder))
        print("(offline: the LLM reranker is a word-overlap stand-in)")

    answerable = sum(not c.get("unanswerable") for c in CASES)
    print(f"{answerable} answerable questions, {len(CASES) - answerable} unanswerable\n")
    print(f"{'chunker':8s} {'search':16s} {'hit@1':>6s} {'hit@4':>6s} {'MRR':>5s}  missed")
    embedder = rag.Embedder()                                       # load the embedding model once
    for chunker in ("fixed", "heading"):
        index = rag.Index.from_folder(chunker=chunker, embedder=embedder)
        modes = [("keyword", "keyword", None), ("vector", "vector", None), ("hybrid", "hybrid", None)]
        if args.rerank and chunker == "heading":
            modes.append((f"hybrid+{args.rerank}", "hybrid", rag.RERANKERS[args.rerank]))
        for name, mode, rerank in modes:
            m = score(index, mode, rerank)
            print(f"{chunker:8s} {name:16s} {m['hit@1']:6.0%} {m['hit@4']:6.0%} {m['mrr']:5.2f}  {'; '.join(m['misses'])}")

    print("\n'I don't know' calibration: best cosine similarity of each question to any chunk")
    index = rag.Index.from_folder(embedder=embedder)
    for kind in ("answerable", "unanswerable"):
        sims = sorted(index.best_similarity(c["question"]) for c in CASES if bool(c.get("unanswerable")) == (kind == "unanswerable"))
        print(f"  {kind:13s} lowest {sims[0]:.2f}  highest {sims[-1]:.2f}")
    print(f"  MIN_SIMILARITY in rag.py = {rag.MIN_SIMILARITY} (questions below it get 'I don't know' with no model call)")


if __name__ == "__main__":
    main()
