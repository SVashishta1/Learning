"""run_evals.py: run the golden set, score it, save the scores, and FAIL if quality dropped (a regression gate).

python run_evals.py                                   # rules system v2 (free baseline), gate against baseline.json
python run_evals.py --system rules --version v1       # an older version: watch the gate catch the regression
python run_evals.py --system llm --version v2 --judge # Claude (or Ollama) + an LLM judge
python run_evals.py --check-judge                     # does the judge agree with human labels? (--offline: stand-in)
python run_evals.py --update-baseline                 # accept the current scores as the new bar
python run_evals.py --system llm --judge --baseline baseline_llm.json   # compare with a separate LLM baseline
Flags: --offline (stand-in judge, no key)  --no-semantic (skip the embedding model)  --no-gate (never exit 1)
"""
import argparse
import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import assistant
import llm
import metrics

HERE = Path(__file__).parent
RESULTS = HERE / "results"


def load_jsonl(name: str) -> list[dict]:
    return [json.loads(line) for line in (HERE / name).open(encoding="utf-8") if line.strip()]


def git_sha() -> str:
    try:
        return subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True,
                              cwd=HERE, timeout=5).stdout.strip() or "local"
    except (OSError, subprocess.TimeoutExpired):
        return "local"


def run(system: str, version: str, use_judge: bool, use_semantic: bool) -> dict:
    cases = load_jsonl("golden_set.jsonl")
    embed = metrics.Embedder() if use_semantic else None
    rows, cost, start = [], 0.0, time.perf_counter()
    for case in cases:
        row = {"id": case["id"], "type": case["type"], "tags": case["tags"]}
        if case["type"] == "triage":
            got, reply = assistant.triage(case["input"], system, version)
            row |= {"got": got, "category": metrics.exact(got["category"], case["expected"]["category"]),
                    "priority": metrics.exact(got["priority"], case["expected"]["priority"])}
            row["passed"] = row["category"] == row["priority"] == 1.0
        else:
            text, reply = assistant.answer(case["input"], system, version)
            idk = metrics.says_idk(text)
            row |= {"got": text, "idk_correct": float(idk == bool(case.get("unanswerable")))}
            if not case.get("unanswerable"):
                facts = metrics.fact_recall(text, case["must_mention"])
                row["facts"] = 0.0 if metrics.has_forbidden(text, case["must_not_mention"]) else facts
                if embed:
                    row["semantic"] = round(metrics.semantic_similarity(text, case["reference"], embed), 3)
            if use_judge:
                verdict = metrics.judge(case["input"], case["reference"], text)
                row |= {"judge": float(verdict.passed), "critique": verdict.critique}
            row["passed"] = row["idk_correct"] == 1.0 and row.get("facts", 1.0) == 1.0 and row.get("judge", 1.0) == 1.0
        cost += reply.cost_usd if reply else 0.0
        rows.append(row)

    def mean(key, kind):
        values = [r[key] for r in rows if r["type"] == kind and key in r]
        return round(sum(values) / len(values), 3) if values else None

    scores = {"triage_category": mean("category", "triage"), "triage_priority": mean("priority", "triage"),
              "answer_facts": mean("facts", "answer"), "answer_semantic": mean("semantic", "answer"),
              "idk_correct": mean("idk_correct", "answer"), "answer_judge": mean("judge", "answer")}
    return {"timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"), "commit": git_sha(),
            "system": system, "version": version, "model": llm.MODEL if system == "llm" else "-",
            "scores": {k: v for k, v in scores.items() if v is not None},
            "cases": len(rows), "passed": sum(r["passed"] for r in rows),
            "cost_usd": round(cost, 4), "seconds": round(time.perf_counter() - start, 1), "rows": rows}


def gate(run_result: dict, baseline: Path) -> list[str]:
    """Compare with the committed baseline. A metric fails if it is lower than baseline - tolerance."""
    if not baseline.exists():
        print(f"\n(No {baseline.name} yet, so nothing to compare with. Create it with --update-baseline.)")
        return []
    base = json.loads(baseline.read_text())
    failures = []
    tolerance = base["tolerance"]                    # how far below the bar is still OK, per metric
    print(f"\nRegression gate vs baseline ({base['system']} {base['version']}):")
    for name, bar in base["scores"].items():
        now = run_result["scores"].get(name)
        if now is None:
            print(f"  {name:16s} baseline {bar:.3f}  now   -    (not measured in this run)")
            continue
        ok = now >= bar - tolerance.get(name, tolerance["default"])
        print(f"  {name:16s} baseline {bar:.3f}  now {now:.3f}  {'✅' if ok else '❌ REGRESSION'}")
        if not ok:
            failures.append(name)
    return failures


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--system", choices=["rules", "llm"], default="rules")
    p.add_argument("--version", choices=["v1", "v2"], default="v2")
    p.add_argument("--judge", action="store_true", help="grade answers with an LLM judge")
    p.add_argument("--offline", action="store_true", help="use the stand-in judge (no API key)")
    p.add_argument("--no-semantic", action="store_true", help="skip semantic similarity (no embedding model)")
    p.add_argument("--no-gate", action="store_true", help="report only; never exit with an error")
    p.add_argument("--check-judge", action="store_true")
    p.add_argument("--update-baseline", action="store_true")
    p.add_argument("--baseline", default="baseline.json", help="which baseline file to compare with / update")
    args = p.parse_args()
    if args.offline:
        from fake_llm import FakeClaude
        if args.system == "llm":
            sys.exit("--offline only replaces the judge. The llm system needs a key or LLM_PROVIDER=ollama.")
        llm.set_client(FakeClaude(responder=metrics.offline_judge_responder))
        print("(offline: the judge is a fact-matching stand-in, not a real model)")

    if args.check_judge:
        result = metrics.judge_agreement(load_jsonl("judge_calibration.jsonl"))
        print(f"Judge vs human labels on {result['n']} examples: agreement {result['agreement']:.0%}, "
              f"false passes {result['false_pass']}, false fails {result['false_fail']}")
        return

    result = run(args.system, args.version, args.judge, not args.no_semantic)
    RESULTS.mkdir(exist_ok=True)
    stamp = result["timestamp"].replace(":", "").replace("+0000", "")
    (RESULTS / f"run-{stamp}-{args.system}-{args.version}.json").write_text(json.dumps(result, indent=2, ensure_ascii=False))
    summary = {k: v for k, v in result.items() if k != "rows"}
    with (RESULTS / "history.jsonl").open("a", encoding="utf-8") as f:
        f.write(json.dumps(summary, ensure_ascii=False) + "\n")

    print(f"System {args.system} {args.version}: {result['passed']}/{result['cases']} cases fully passed "
          f"in {result['seconds']} s, cost ${result['cost_usd']}")
    for name, value in result["scores"].items():
        print(f"  {name:16s} {value:.3f}")
    failed = [r for r in result["rows"] if not r["passed"]]
    if failed:
        print("Failed cases:")
        for r in failed:
            print(f"  {r['id']:7s} [{', '.join(r['tags'])}] got: {json.dumps(r['got'], ensure_ascii=False)[:70]}")

    baseline = HERE / args.baseline
    if args.update_baseline:
        baseline.write_text(json.dumps({"system": args.system, "version": args.version, "scores": result["scores"],
                                        "tolerance": {"default": 0.02, "answer_semantic": 0.10}}, indent=2) + "\n")
        print(f"\nBaseline updated -> {baseline.name}")
        return
    regressions = gate(result, baseline)
    if regressions and not args.no_gate:
        print(f"\n❌ Quality dropped on: {', '.join(regressions)}. Failing the build.")
        sys.exit(1)
    print("\n✅ No regressions.")


if __name__ == "__main__":
    main()
