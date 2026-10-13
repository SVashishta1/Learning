# 8.1 · Writer + critic: the reflection loop

**What you build:** two agents. The **Writer** drafts something (a LinkedIn post, cover letter, product description...). The **Critic** scores it 1–10 using a strict schema and lists concrete fixes. The Writer revises, and the loop repeats until the score reaches 8 or after 3 rounds. You see the score climb round by round.
**Like you're 10:** you write an essay, your toughest teacher marks it in red pen, you rewrite it. Two or three rounds and it's way better than your first try. Here both the student and the teacher are AIs.

## Run it
```bash
cd level-8-multi-agent-systems/01-writer-and-critic-reflection-loop
pip install -r requirements.txt
export ANTHROPIC_API_KEY=sk-ant-...
python writer_critic.py
python writer_critic.py "a friendly 100-word email asking my manager for 2 days off next week"
```
The final text and the scores go to `output.md`, and you get a per-agent cost report.

Tests (offline): `pytest -v`

## Key ideas
- **Evaluator-optimizer pattern:** separate *generating* from *judging*. A critic with a rubric catches problems the writer can't see in its own work.
- **Structured critique (`Critique` schema):** a numeric score makes the loop controllable (`if score >= 8: stop`), and the `fixes` list makes the feedback actionable.
- **Stopping rules:** always cap rounds. Critics can be never-satisfied, and every round costs tokens.
- **Different system prompts = different "people"**, even on the same model.
- `agent_core.py` is shared by all of Level 8. Read it now; it's short.

## Your turn
1. Give the critic a specific rubric (e.g. "must mention a number", "no word longer than 3 syllables").
2. Make the critic a *different* model (`Agent(..., client=...)` with `CLAUDE_MODEL` swapped). Do cheaper critics still help?
3. Turn it into a code-writing loop: Writer writes a Python function, a "Tester" runs it against test cases and feeds back failures. (That's how AI coding tools self-correct.)

## Read
- Evaluator-optimizer workflow: https://www.anthropic.com/engineering/building-effective-agents
