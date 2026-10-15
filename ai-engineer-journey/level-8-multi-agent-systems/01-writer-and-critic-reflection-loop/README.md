# 8.1 · Writer + critic: the reflection loop

**What you'll build:** two agents. The **Writer** drafts something (a LinkedIn post, a cover letter, a product description...). The **Critic** scores it 1–10 with a strict schema and lists concrete fixes. The Writer revises, and the loop repeats until the score reaches 8 or 3 rounds have passed. You watch the score climb round by round, and get a cost report per agent.
**Like you're 10:** you write an essay, your toughest teacher marks it in red pen, you rewrite it. Two or three rounds and it's way better than your first try. Here both the student and the teacher are AIs.
**Time:** ~1.5 h · **Builds on:** [7.6 Capstone](../../level-7-real-world-ai-apps/06-capstone-deploy-a-full-ai-app) (and the agent loop from [7.4](../../level-7-real-world-ai-apps/04-ai-agent-with-tools-calculator-weather-search)) · **Needs:** an Anthropic API key (tests run without one)

## Why this matters
A first draft from any model is rarely its best work, just like with people. Splitting "make it" from "judge it" is one of the simplest, most reliable ways to raise quality, and it's used for marketing copy, code generation, translations and reports. It's also your first **multi-agent system**: two "people" with different jobs, built from the same model with different system prompts. Every project in Level 8 builds on the `agent_core.py` toolkit you meet here.

## What you'll learn
- **Evaluator-optimizer (reflection) pattern**: one agent generates, another evaluates, and the feedback drives the next version.
- **Structured critique**: a schema with a numeric `score` your code can act on and a `fixes` list the writer can apply.
- **Stopping rules**: stop at a target score *or* after a maximum number of rounds, because critics can be never satisfied and each round costs money.
- **Agents as roles**: the same model becomes a different "person" with a different system prompt.
- **`agent_core.py`**: the shared toolkit for Level 8 (agent loop, tools, human approval, structured answers, cost tracking).

## Before you start
```bash
cd level-8-multi-agent-systems/01-writer-and-critic-reflection-loop
pip install -r requirements.txt
```
- `anthropic`: calls Claude. `pydantic`: the `Critique` schema. `pytest`: tests.

**API key:** set `ANTHROPIC_API_KEY` as in the [Level 7 README](../../level-7-real-world-ai-apps/README.md#api-key-needed-from-here-on). Multi-agent runs make several calls, so while learning use `export CLAUDE_MODEL=claude-haiku-5-5` (a full run then costs a fraction of a cent).

## Run it
1. From the course root: `cd level-8-multi-agent-systems/01-writer-and-critic-reflection-loop`
2. Tests (offline): `pytest -v`
3. The default brief (a LinkedIn post about your RAG app): `python writer_critic.py`
4. Your own brief: `python writer_critic.py "a friendly 100-word email asking my manager for 2 days off next week"`

### What you should see
(Representative: scores, fixes and text change every run. Agent names appear in colour.)
```
[Writer] ▶ Write this: a 120-word LinkedIn post announcing that I finished building a RAG app that answers questions about a compan
[Writer] ✔ done (208 chars)
[Critic] 📋 Critique: score=5 strengths=['Clear announcement', 'Right topic for recruiters'] fixes=["Say what the app does in one concrete...

📝 Round 1: score 5/10
   - Say what the app does in one concrete sentence (e.g. 'answers HR questions with page citations')
   - Replace 'great learning journey' with one specific skill you learned
   - Cut the hashtags to at most two relevant ones
   - End with a clear call to action (link to the repo or demo)
[Writer] ▶ <brief>a 120-word LinkedIn post announcing that I finished building a RAG app that answers questions about a company han
[Writer] ✔ done (742 chars)
[Critic] 📋 Critique: score=8 strengths=['Concrete and specific', 'Shows real skills', 'Clear call to action'] fixes=['Optionally mention...

📝 Round 2: score 8/10
   - Optionally mention the evaluation results

============================================================
FINAL
============================================================
I just shipped a RAG app that answers questions about a 40-page company handbook, citing the exact page for every answer. ...

Token usage per agent:
  Writer                    1210 in /    420 out  ≈ $0.0132
  Critic                    1530 in /    310 out  ≈ $0.0123
  TOTAL                  ≈ $0.0256
```
What to look at: the fixes are specific ("cut the hashtags to two"), not vague ("make it better"); the score rises after the Writer applies them; the loop stops as soon as the target is reached. `output.md` gets the brief, the score history and the final text.

## How it works
```
brief ─► Writer.run() ─► draft ─► Critic.ask_structured(Critique) ─► score + fixes
                           ▲                                            │
                           └──── Writer.run("apply these fixes") ◄──────┘  (until score ≥ 8 or 3 rounds)
```

### `agent_core.py` (shared by all of Level 8, read it once)
1. **`Tool`** bundles a name, a description, a Pydantic `input_model` and the Python function `fn`. `definition()` turns it into the JSON the API expects. `needs_approval=True` makes the agent ask a human before running it (used in 8.7).
2. **`Agent`** holds a `name`, a `system` prompt, its `tools`, an optional `model` (empty = `CLAUDE_MODEL`), `max_steps`, `effort` and token counters. `__post_init__` creates the client and picks a fixed colour for its log lines.
3. **`Agent.run(task)`** is the 7.4 agent loop: call Claude with the tools, append the reply, run any `tool_use` blocks through `_call_tool()`, send all results back in one message, repeat until there are no more tool calls (or `max_steps`).
4. **`_call_tool()`** validates the arguments with the tool's Pydantic model, asks the `approver` if the tool is risky, runs it, and turns any exception into an `is_error` result the model can react to.
5. **`ask_structured(prompt, Model)`** is a single call with structured output: you get a validated Pydantic object back. Perfect for scores, routing decisions and plans.
6. **`cost_report(agents)`** multiplies each agent's tokens by its model's price per million tokens.

### `writer_critic.py`
1. **`Critique`** is the schema: `score` (1–10), up to 3 `strengths`, up to 5 `fixes` (most important first) and `ready`. The field descriptions tell the Critic exactly what to fill in.
2. **`WRITER`** and **`CRITIC`** are two `Agent`s with different system prompts: the Writer must apply every fix and output only the text; the Critic is "demanding but fair" and saves 9–10 for genuinely excellent work.
3. **`write_with_feedback(brief, target=8, max_rounds=3)`**: the Writer drafts; then for each round the Critic grades the draft (brief and draft wrapped in `<brief>`/`<draft>` tags so they can't be confused with instructions). The score and fixes are recorded and printed. If `score >= target` or `ready`, stop; otherwise the Writer rewrites with the fixes as a bullet list. If round 3 still misses the target, the Writer applies that last round's fixes once more and the loop ends anyway.
4. **`__main__`** takes the brief from the command line (or a default), runs the loop, prints the final text, writes `output.md` and prints `cost_report([WRITER, CRITIC])`.
5. **Tests**: `test_writer_critic.py` scripts a 5 then a 9 and checks the loop stops and that the Critic's fix reached the Writer. `test_agent_core.py` checks the tool loop, declined approvals, invalid arguments and per-agent models.

## If something goes wrong
- **`anthropic.AuthenticationError`** → set `ANTHROPIC_API_KEY` in this terminal.
- **Strange symbols like `[96m` around agent names** → your terminal doesn't show colours (old Windows `cmd`). Use Windows Terminal or VS Code's terminal, or set `COLORS = [""]` in `agent_core.py`.
- **The score never reaches 8** → that's what `max_rounds` is for. Read the fixes: if they contradict the brief, the brief is unclear. If the critic is too harsh, lower `target` or soften its system prompt.
- **The Writer adds "Here's the revised draft:" before the text** → strengthen its system prompt ("Output only the text itself, with no introduction"), or strip such lines in code.
- **It's slower and pricier than expected** → each round is 2 calls, each with the full draft. Use `CLAUDE_MODEL=claude-haiku-5-5` while experimenting.

## Try this
1. **A stricter rubric.** Make the Critic check specific rules: "must include one number", "no hashtags", "under 120 words". Does the final text follow them?
   <details><summary>Hint</summary>

   Add the rules to `CRITIC`'s system prompt as a numbered checklist and say "score at most 6 if any rule is broken". You can also add a field to `Critique`, e.g. `broken_rules: list[str]`, and print it each round. Rules a program can check (word count) are even better checked in Python, like `check_math()` in 7.2.
   </details>
2. **A cheaper critic.** Give the Critic its own model, keep the Writer on the default, and compare scores and the cost report.
   <details><summary>Solution</summary>

   ```python
   CRITIC = Agent("Critic", system=(...), effort="medium", model="claude-haiku-5-5")
   ```
   `cost_report` uses each agent's own model price. Mixing models per role (a strong model where quality matters, a cheap one for checking or routing) is a standard way to cut costs.
   </details>
3. **A self-correcting coder.** Turn it into a code loop: the Writer writes a Python function `is_palindrome(s)`, and instead of the Critic, *your code* runs test cases and feeds back the failures.
   <details><summary>Solution</summary>

   ```python
   TESTS = [("racecar", True), ("A man, a plan, a canal: Panama", True), ("hello", False)]

   code = WRITER.run("Write a Python function is_palindrome(s) that ignores case, spaces and punctuation. "
                     "Output only the code, no backticks.")
   for round_no in range(3):
       namespace = {}
       exec(code, namespace)                       # fine for your own experiment; NEVER exec untrusted code on a server
       failures = [f"is_palindrome({s!r}) should be {want}" for s, want in TESTS
                   if namespace["is_palindrome"](s) != want]
       print(f"Round {round_no + 1}: {len(failures)} failures")
       if not failures:
           break
       code = WRITER.run(f"<code>\n{code}\n</code>\nThese tests fail:\n" + "\n".join(failures) + "\nFix the code. Output only the code.")
   ```
   A test runner is the best critic of all: it's never vague and never wrong. This is how AI coding tools self-correct.
   </details>

## Check yourself
1. Why use a separate Critic instead of asking the Writer "please improve your text"?
2. What does the numeric `score` let your code do that free-text feedback can't?
3. Why must the loop have `max_rounds`, even if the target is reasonable?
4. Name a task where a program (not an LLM) should be the critic.

<details><summary>Answers</summary>

1. A dedicated critic with its own instructions and rubric looks at the text fresh and is told to find problems. The writer tends to defend its own choices, and a separate role makes the feedback explicit and checkable.
2. Decide automatically: `if score >= 8: stop`. You can also log scores, compare models, and alert when quality drops.
3. A critic can always find something, and each round costs tokens and time. Without a cap, a picky critic means an endless (and expensive) loop.
4. Anything with an objective check: code (run the tests), maths (recompute it), JSON (validate the schema), word limits (count the words).
</details>

## Learn more (optional)
- Building effective agents, evaluator-optimizer workflow (Anthropic): https://www.anthropic.com/engineering/building-effective-agents
- Reflection agents explained: https://www.youtube.com/results?search_query=reflection+agent+llm+self+critique

## Next
→ [8.2 · Customer-support router + specialists](../02-customer-support-router-and-specialists)
