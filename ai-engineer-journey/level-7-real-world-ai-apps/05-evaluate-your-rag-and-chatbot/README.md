# 7.5 · Evaluate your RAG and chatbot

**What you'll build:** an evaluation harness for the RAG app from 7.3:
1. a **test set** (14 questions with known answers, including 2 trick questions that *can't* be answered),
2. **retrieval metrics** (hit rate, MRR) comparing chunk sizes, free and offline,
3. answer checks with **keywords** and an **LLM-as-judge** (Claude grades correctness and faithfulness with a strict schema),
4. **latency and cost** per run, saved to `results/report.json`.

**Like you're 10:** you built a robot that answers questions. How do you *know* it's good? You write an exam with an answer key, let the robot take it, and grade it: first with a simple checklist (does the answer contain "25"?) and then with a strict teacher (the judge). Change one thing, re-take the exam, and see if it got better or worse.
**Time:** ~2 h · **Builds on:** [7.3 RAG](../03-rag-ask-questions-about-your-pdfs) and [7.4 AI agent with tools](../04-ai-agent-with-tools-calculator-weather-search) · **Needs:** nothing for the retrieval part; an Anthropic API key for the full eval (~28 calls, cents with Haiku)

## Why this matters
"If you can't measure it, you can't improve it." Every prompt tweak, model switch or chunk-size change can make some answers better and others silently worse. Teams that ship reliable AI run an eval before and after every change, just like unit tests. Being able to say "accuracy went from 86% to 93% and cost dropped 40%" is one of the most valued (and most underrated) AI engineering skills.

## What you'll learn
- **Eval set**: a fixed list of questions with expected answers, including ones the system *should* refuse.
- **Retrieval metrics**: hit rate (was the right passage found?) and MRR (how high was it ranked?), measured without any LLM.
- **LLM-as-judge**: using a model with a strict schema to grade answers for correctness and faithfulness.
- **Faithfulness**: whether every claim is supported by the sources (the opposite of hallucination).
- **Latency and cost tracking**: measuring speed and money per run so you can compare options fairly.

## Before you start
```bash
cd level-7-real-world-ai-apps/05-evaluate-your-rag-and-chatbot
pip install -r requirements.txt
```
- `anthropic`: calls Claude (answers and judge). `pydantic`: the judge's verdict schema.
- `numpy`, `scikit-learn`, `sentence-transformers`, `pypdf`: the RAG pipeline (same `rag.py` as 7.3).
- `pytest`: tests.

**API key:** only for the full eval. Set `ANTHROPIC_API_KEY` as in the [Level 7 README](../README.md#api-key-needed-from-here-on). `--retrieval-only` and the tests are free and offline.

## Run it
1. From the course root: `cd level-7-real-world-ai-apps/05-evaluate-your-rag-and-chatbot`
2. Tests (offline): `pytest -v`
3. Retrieval experiment (free): `python evaluate.py --retrieval-only`
4. Full eval: `python evaluate.py` (cheapest: `CLAUDE_MODEL=claude-haiku-5-5 python evaluate.py`)

### What you should see
Retrieval experiment (real output from the TF-IDF fallback; with sentence-transformers your numbers may differ slightly):
```
== Retrieval experiment (offline) ==
chunk size | k | hit rate | MRR
       200 | 1 |   100%   | 1.00
       200 | 3 |   100%   | 1.00
       600 | 1 |   92%   | 0.92
       600 | 3 |   100%   | 0.96
      1500 | 1 |   100%   | 1.00
      1500 | 3 |   100%   | 1.00
```
Full eval (representative; latency, wording and cost vary):
```
== Full evaluation with claude-opus-5-5 ==
✅  2.1s | How many days of paid annual leave do full-time employees ge
✅  1.8s | Until when can carried-over vacation days be used?
...
❌  2.4s | What happens if I submit an expense 4 months late?
...
✅  1.6s | What is the CEO's salary?
✅  1.5s | Does the company offer free gym membership?

SUMMARY: {
  "keyword_accuracy": 0.929,
  "judge_accuracy": 0.929,
  "faithfulness": 1.0,
  "avg_latency_s": 1.95,
  "answer_cost_usd": 0.0179
}
Details saved to results/report.json
```
What to look at:
- With chunk size 600 and k=1, one question's key fact landed in the *second* chunk: hit rate drops to 92% and MRR to 0.92. Raising k to 3 fixes it. This is exactly the kind of trade-off evals reveal.
- A ❌ on one question: open `results/report.json` and read its `reason` to see *why* the judge failed it.
- `keyword_accuracy` and `judge_accuracy` can disagree: "aren't reimbursed" fails the keyword check for `"not be reimbursed"` but a judge accepts it. Keywords are cheap but brittle; judges are flexible but cost money.
- The two trick questions pass only if the bot admits it couldn't find the answer.

## How it works
```
eval_set.jsonl ──► retrieval_metrics() ─► hit rate, MRR           (no LLM, free)
               └─► run_full(): for each case
                      answer() (from rag.py) ─► keyword check
                                             └► judge() ─► Verdict{correct, faithful, reason}
                   ─► summary: accuracy, faithfulness, latency, cost ─► results/report.json
```

1. **`eval_set.jsonl`** has one JSON object per line: the `question`, the words the answer `must_include`, the `source` document that holds the fact, and `"unanswerable": true` for the two trick questions. `CASES` loads it.
2. **`retrieval_metrics(index, k)`** skips the unanswerable cases. For each question it looks at the top k chunks and marks a **hit** if a chunk comes from the right document *and* contains the key fact. **MRR** (mean reciprocal rank) rewards finding it early: 1st place scores 1, 2nd place 0.5, 3rd 0.33, averaged over all questions.
3. **`main()`** first loads one `Embedder` and rebuilds the index with chunk sizes 200, 600 and 1500 (overlap = 1/5 of the size), printing hit rate and MRR for k = 1 and 3. With `--retrieval-only` it stops there.
4. **`Verdict`** is the judge's schema: `correct`, `faithful` and a one-sentence `reason`. **`judge(client, case, result)`** sends the question, the answer and the cited sources (plus a note for trick questions that "I don't know" is the right behaviour) to `llm.parse(..., output_format=Verdict)`. The `JUDGE_SYSTEM` prompt asks for strictness, and structured output makes every grade machine-readable.
5. **`run_full(client, index)`** answers every case with `rag.answer()`, times it with `time.perf_counter()`, adds up tokens, runs the keyword check (for trick questions: does it say "couldn't find"?), asks the judge, and prints ✅/❌ per question.
6. **The summary** averages each metric and turns tokens into dollars with `PRICES` (per million tokens). The judge's own calls are *not* included in `answer_cost_usd`: that's the cost of the product, not of testing it. Everything is saved to `results/report.json`.
7. **`test_evaluate.py`** checks the retrieval metrics are sensible offline and that `judge()` really sends the question, answer and sources (using `FakeClient`).

## If something goes wrong
- **`FileNotFoundError: eval_set.jsonl`** → run the script from this project's folder (the `cd` line above).
- **`(No sentence-transformers model: ...)` message** → the embedding model couldn't be downloaded, so TF-IDF is used. Results are still valid for comparing settings; check your internet to use the real model.
- **`(No price listed for ...)` and a cost of 0** → you set `CLAUDE_MODEL` to a model missing from `PRICES`. Add its input/output prices per million tokens.
- **`anthropic.RateLimitError`** → new accounts have low rate limits and the eval makes ~28 calls quickly. Wait a minute and re-run, or use Haiku. The SDK already retries twice automatically.
- **Judge results change between runs** → LLM grading is a bit noisy. Compare averages over the whole set, re-run borderline cases, and spot-check a few verdicts yourself.

## Try this
1. **Harder questions.** Add 5 multi-hop questions that need two facts, e.g. "If I fly 12 hours to Tokyo and stay 3 nights, what's my max hotel + meal budget?" (Tokyo is a major city: 3 × 180 + 3 × 60 = 720 euros).
   <details><summary>Hint</summary>

   Add lines like `{"question": "...", "must_include": ["720"], "source": "expense_policy.md"}`. Multi-hop questions usually fail more: the facts may be in different chunks (retrieval) and the model must combine them correctly (generation). Check `retrieved` in `report.json` to see which half failed.
   </details>
2. **Model shoot-out.** Run the full eval with `CLAUDE_MODEL=claude-haiku-5-5` and with the default model. Make a small table: accuracy, faithfulness, latency, cost.
   <details><summary>Hint</summary>

   Rename `results/report.json` after the first run so the second doesn't overwrite it. On simple, well-retrieved questions a small model is often nearly as accurate for a fraction of the cost. That's the kind of decision an eval lets you make with evidence instead of guesses.
   </details>
3. **Break it on purpose.** In `rag.py`, delete the rule "Use ONLY the numbered sources provided..." from `SYSTEM` and add "Answer from your general knowledge if needed." Re-run. What happens to the trick questions and to faithfulness?
   <details><summary>Hint</summary>

   The trick questions usually start failing (the model guesses a typical CEO salary or gym perk) and faithfulness drops. This is a *regression*, and your eval caught it. Restore the rule afterwards. This is why you run evals after every prompt change.
   </details>

## Check yourself
1. Hit rate is 100% but judge accuracy is 70%. Which part of the system should you work on?
2. Why include questions that can't be answered from the documents?
3. What's the difference between "correct" and "faithful"? Give an example of an answer that is correct but not faithful.
4. Why is the judge given a strict schema (`Verdict`) instead of being asked "is this good?"

<details><summary>Answers</summary>

1. Generation: the right passages are being found, but the model answers badly. Improve the prompt, the model choice or how sources are presented.
2. To test that the system admits ignorance instead of hallucinating. A bot that confidently invents HR policies is worse than one that says "I couldn't find that".
3. Correct = right answer to the question; faithful = every claim is backed by the sources. Example: "Paris is the capital of France and the hotel limit there is 180 euros" when the sources only mention the hotel limit: correct, but the extra claim isn't from the sources.
4. Structured yes/no fields are consistent and can be counted automatically; a free-text opinion would vary in format and be hard to turn into a score.
</details>

## Learn more (optional)
- Anthropic, define success criteria and build evals: https://platform.claude.com/docs/en/test-and-evaluate/develop-tests
- Hamel Husain, "Your AI product needs evals": https://hamel.dev/blog/posts/evals/
- LLM evaluation explained: https://www.youtube.com/results?search_query=llm+evaluation+llm+as+a+judge+explained

## Next
→ [7.6 · Capstone: deploy a full AI app (auth, limits, metrics, CI)](../06-capstone-deploy-a-full-ai-app)
