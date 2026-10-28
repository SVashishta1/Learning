"""ask.py: ask Northwind's policy documents a question and get a cited answer (or an honest "I don't know").

python ask.py "Can I send UN3481 batteries?" --offline         # free: real search, stand-in answer writer
python ask.py "How cold do you keep frozen stuff?"             # with Claude (or LLM_PROVIDER=ollama)
python ask.py "..." --rerank llm                               # add the reranking step (llm | cross-encoder | none)
"""
import argparse

import llm
import rag


def main():
    parser = argparse.ArgumentParser(description="Ask the Northwind policy documents a question.")
    parser.add_argument("question")
    parser.add_argument("--offline", action="store_true", help="use the word-overlap stand-in instead of a real model")
    parser.add_argument("--rerank", choices=list(rag.RERANKERS), default="none")
    parser.add_argument("--k", type=int, default=4, help="how many chunks to give the model")
    args = parser.parse_args()
    if args.offline:
        from fake_llm import FakeClaude
        llm.set_client(FakeClaude(responder=rag.offline_responder))
        print("(offline: search is real; the answer writer is a word-overlap stand-in, not a real model)\n")

    index = rag.Index.from_folder()
    print(f"Indexed {len(index.chunks)} chunks from {rag.DOCS.name}/\n")
    hits = index.search(args.question, args.k, rerank=rag.RERANKERS[args.rerank])
    print("RETRIEVED (rank: keyword rank / vector rank -> fused score)")
    for n, h in enumerate(hits, start=1):
        ranks = " / ".join(f"{name} {h.ranks.get(name, '-')}" for name in ("keyword", "vector"))
        extra = f" / rerank {h.ranks['rerank']}" if "rerank" in h.ranks else ""
        print(f"  [{n}] {ranks}{extra} -> {h.score:<7} {h.chunk.label}")

    result = rag.answer(index, args.question, args.k, rerank=rag.RERANKERS[args.rerank])
    print(f"\nANSWER (best similarity {result['similarity']}):\n  {result['answer']}")
    for s in result["sources"]:
        print(f"  [{s['n']}] {s['label']}")
    if result["stopped_by"]:
        print(f"  (stopped by: {result['stopped_by']})")
    for p in result["problems"]:
        print(f"  ⚠️  {p}")


if __name__ == "__main__":
    main()
