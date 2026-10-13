"""Project 7.5: evaluate a RAG system like a professional.

python evaluate.py --retrieval-only     # free + offline: compares chunk sizes and k on retrieval metrics
python evaluate.py                      # full eval with Claude: answers + LLM-as-judge + latency + cost
"""
import json
import sys
import time
from pathlib import Path

from pydantic import BaseModel, Field

import llm
from rag import Embedder, Index, answer

# $ per 1M tokens (input, output). Check current prices: https://platform.claude.com/docs/en/about-claude/pricing
PRICES = {"claude-opus-5-5": (4.0, 20.0), "claude-sonnet-5-5": (2.0, 10.0), "claude-haiku-5-5": (0.10, 0.50)}
CASES = [json.loads(line) for line in open("eval_set.jsonl")]


# ---------- 1. Retrieval metrics (no LLM needed) ----------
def retrieval_metrics(index: Index, k: int) -> dict:
    answerable = [c for c in CASES if not c.get("unanswerable")]
    hits, rr = 0, 0.0
    for case in answerable:
        # A "hit" = a retrieved chunk from the right document that actually CONTAINS the key fact.
        found = [chunk.source == case["source"] and case["must_include"][0].lower() in chunk.text.lower()
                 for chunk, _ in index.search(case["question"], k)]
        if any(found):
            hits += 1
            rr += 1 / (found.index(True) + 1)                   # reciprocal rank: 1st place = 1, 2nd = 0.5 ...
    return {"hit_rate": hits / len(answerable), "mrr": rr / len(answerable)}


# ---------- 2. LLM-as-judge ----------
class Verdict(BaseModel):
    correct: bool = Field(description="Does the answer correctly answer the question according to the sources?")
    faithful: bool = Field(description="Is every claim in the answer supported by the sources (no made-up facts)?")
    reason: str = Field(description="One sentence explaining the verdict")


JUDGE_SYSTEM = "You are a strict grader of question-answering systems. Judge only against the provided sources."


def judge(client, case, result) -> Verdict:
    sources = "\n".join(f"[{s['n']}] {s['text']}" for s in result["sources"]) or "(no sources cited)"
    prompt = (f"Question: {case['question']}\n\nAnswer given:\n{result['answer']}\n\nSources the answer cited:\n{sources}\n\n"
              + ("This question is NOT answerable from the documents: the correct behaviour is to say so." if case.get("unanswerable") else ""))
    return llm.parse(client, max_tokens=1000, system=JUDGE_SYSTEM, output_format=Verdict,
                     messages=[{"role": "user", "content": prompt}], output_config={"effort": "low"}).parsed_output


# ---------- 3. Full evaluation ----------
def run_full(client, index, k=4) -> dict:
    rows, total_in, total_out = [], 0, 0
    for case in CASES:
        start = time.perf_counter()
        result = answer(client, index, case["question"], k)
        latency = time.perf_counter() - start
        total_in += result["usage"]["input_tokens"]; total_out += result["usage"]["output_tokens"]
        text = result["answer"].lower()
        if case.get("unanswerable"):
            keyword_ok = "couldn't find" in text or "could not find" in text or "not mention" in text
        else:
            keyword_ok = all(word.lower() in text for word in case["must_include"])
        verdict = judge(client, case, result)
        rows.append({"question": case["question"], "keyword_ok": keyword_ok, "judge_correct": verdict.correct,
                     "faithful": verdict.faithful, "latency_s": round(latency, 2), "reason": verdict.reason})
        print(f"{'✅' if verdict.correct else '❌'} {latency:4.1f}s | {case['question'][:60]}")
    price_in, price_out = PRICES.get(llm.MODEL, (0, 0))
    n = len(rows)
    return {"rows": rows, "summary": {
        "keyword_accuracy": sum(r["keyword_ok"] for r in rows) / n,
        "judge_accuracy": sum(r["judge_correct"] for r in rows) / n,
        "faithfulness": sum(r["faithful"] for r in rows) / n,
        "avg_latency_s": round(sum(r["latency_s"] for r in rows) / n, 2),
        "answer_cost_usd": round((total_in * price_in + total_out * price_out) / 1e6, 4)}}


def main():
    print("== Retrieval experiment (offline) ==")
    print("chunk size | k | hit rate | MRR")
    for size in (200, 600, 1500):
        index = Index(Embedder()).build("docs", size=size, overlap=size // 5)
        for k in (1, 3):
            m = retrieval_metrics(index, k)
            print(f"{size:10d} | {k} |   {m['hit_rate']:.0%}   | {m['mrr']:.2f}")
    if "--retrieval-only" in sys.argv:
        return
    print(f"\n== Full evaluation with {llm.MODEL} ==")
    report = run_full(llm.get_client(), Index(Embedder()).build("docs"))
    Path("results").mkdir(exist_ok=True)
    Path("results/report.json").write_text(json.dumps(report, indent=2))
    print("\nSUMMARY:", json.dumps(report["summary"], indent=2))
    print("Details saved to results/report.json")


if __name__ == "__main__":
    main()
