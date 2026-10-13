# 7.5 · Evaluate your RAG and chatbot

**What you build:** an evaluation harness for the RAG app from 7.3:
1. a **test set** (14 questions with known answers, including 2 trick questions that *can't* be answered),
2. **retrieval metrics** (hit rate, MRR) comparing chunk sizes, free and offline,
3. answer checks with **keywords** and an **LLM-as-judge** (Claude grades correctness and faithfulness using a strict schema),
4. **latency and cost** per run, saved to `results/report.json`.

**Like you're 10:** you built a robot that answers questions. How do you *know* it's good? You write an exam with an answer key, let the robot take it, and grade it: first with a simple checklist (does the answer contain "25"?) and then with a strict teacher (the judge). Change one thing and re-take the exam to see if it got better or worse.

> "If you can't measure it, you can't improve it." Teams that ship AI successfully all have evals. This is the most underrated skill for AI engineers.

## Run it
```bash
cd level-7-real-world-ai-apps/05-evaluate-your-rag-and-chatbot
pip install -r requirements.txt
python evaluate.py --retrieval-only        # free: which chunk size / k retrieves best?
export ANTHROPIC_API_KEY=sk-ant-...
python evaluate.py                         # full eval (~30 API calls; cents with Haiku)
```
Tests (offline): `pytest -v`

## Key ideas
| Metric | What it tells you | Needs LLM? |
|--------|-------------------|------------|
| Hit rate @k | was a chunk containing the key fact (from the right document) among the top k? | no |
| MRR | how high was it ranked? | no |
| Keyword accuracy | does the answer contain the key fact? (cheap, strict, brittle) | answers only |
| Judge accuracy | is the answer correct? (flexible, needs a good rubric) | yes |
| Faithfulness | did it invent anything not in the sources? | yes |
| Unanswerable handling | does it admit "I don't know"? | yes |
| Latency / cost | can we afford it, and is it fast enough? | measured |

- **Separate retrieval from generation:** when an answer is wrong, the metrics tell you *which half* broke.
- **LLM-as-judge with structured output** gives consistent, machine-readable grades. Spot-check the judge against your own judgement sometimes.
- **Regression testing:** run the eval before and after every prompt or model change, the same way unit tests work.

## Your turn
1. Add 10 harder questions (multi-hop: "If I fly 12 hours to Tokyo and stay 3 nights, what's my max hotel + meal budget?").
2. Run the full eval with `CLAUDE_MODEL=claude-haiku-5-5` and with the default model. Compare accuracy vs. cost.
3. Make the system prompt in `rag.py` worse on purpose (remove "only use the sources") and watch faithfulness drop.

## Read
- Anthropic, define success criteria and build evals: https://platform.claude.com/docs/en/test-and-evaluate/develop-tests
- Hamel Husain, "Your AI product needs evals": https://hamel.dev/blog/posts/evals/
