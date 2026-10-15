# 29 · Two AIs: writer and critic

**What you'll build:** a **team of two**. The writer AI drafts a text, the critic AI scores it from 1 to 10 and lists what to fix, and the writer improves it. This repeats until the score reaches 8 (or after 3 rounds), and you watch the score go up.
**Time:** ~45 min · **Builds on:** [28 · Agent with many tools](../28-agent-with-many-tools) and `ask_for_data` from [20 · AI turns messy text into data](../../part-4-chatbots/20-ai-turns-messy-text-into-data) · **Needs:** an Anthropic API key

## Why this matters
An AI rarely spots the weak points in its own first draft, but a second AI with a different job (and a strict brief) often does. This "generate, then evaluate, then improve" pattern is used for writing, code review, translation and checking AI answers before users see them. It is also your first **multi-agent** system: same model, two roles.

## What you'll learn
- **Role (system prompt):** the same AI behaves like a different expert depending on its instructions.
- **Structured feedback:** the critic must fill in a form (`Review`: a score and a list of fixes), so your code can read the score and decide what to do.
- **Feedback loop:** write → review → improve, repeated until the work is good enough.
- **Stopping rule:** stop when the score is high enough *or* after a fixed number of rounds, so it can't run (and cost) forever.

## Before you start
- Install the Part 6 packages (once):
  ```bash
  pip install anthropic chromadb pypdf fastapi "uvicorn[standard]" python-multipart httpx tzdata
  ```
  This lesson only needs `anthropic` (Claude) and `pydantic` (describes the critic's form; it comes with `anthropic`).
- Set your API key in this terminal (full steps in the [Part 4 README](../../part-4-chatbots)):
  ```bash
  export ANTHROPIC_API_KEY=sk-ant-your-key-here        # Mac
  $env:ANTHROPIC_API_KEY="sk-ant-your-key-here"        # Windows PowerShell
  ```

## Run it
1. From the course folder (`Learning/ai-from-zero`), with your venv switched on:
   ```bash
   cd part-6-ai-agents-and-teams/29-two-ais-writer-and-critic
   python writer_and_critic.py
   ```
2. Give it your own writing task:
   ```bash
   python writer_and_critic.py "A short, friendly email asking my landlord to fix the heating"
   ```

### What you should see
```
--- Round 1: score 6/10 ---
   • The opening is generic; start with a specific moment.
   • Say what the chatbot actually does.
   • Cut the exclamation marks.

--- Round 2: score 7/10 ---
   • Add one concrete thing you learned (e.g. how chat memory works).
   • End with a question to invite comments.

--- Round 3: score 8/10 ---
   • Strong and specific. Optionally add a link to the project.

✨ FINAL VERSION:
Three weeks ago I couldn't write a for-loop. Last night, a chatbot I built answered its first
question in a web page I made myself. ...
```
Your scores, feedback and text will differ every run. Look for the score rising, and check whether the final version really fixed the points the critic listed. Sometimes the first draft already scores 8 and it stops after round 1.

## How it works
```
task ──► WRITER ──draft──► CRITIC ──{score, feedback}──► score ≥ 8? ──yes──► ✨ final
              ▲                                              │ no
              └──────── "improve it using this feedback" ◄───┘   (at most 3 rounds)
```
1. `class Review(BaseModel)` is the critic's form: a whole number `score` and a list of strings `feedback`. (A Pydantic `BaseModel` is a Python class that describes the shape of some data.)
2. `WRITER` and `CRITIC` are the two system prompts. Same model, different jobs: the writer is told to write concretely and output only the text; the critic is told to be strict ("10 = perfect, rare") and give 2–4 specific, fixable points.
3. `task` is what you typed, or a default LinkedIn post. `draft = ai.ask(task, system=WRITER)` makes the first draft.
4. The loop `for round_number in range(1, 4):` runs at most 3 times:
   - `ai.ask_for_data(..., Review, system=CRITIC)` sends the task and the draft to the critic and gets back a **filled-in `Review` object**, not free text, so `review.score` is a real number your code can compare.
   - It prints the score and each feedback point.
   - `if review.score >= 8: break` stops early when the draft is good enough.
   - Otherwise the writer gets the task, its own draft and the feedback, and writes an improved draft.
5. After the loop, the final draft is printed. (If round 3 still scores under 8, the writer improves it once more using that last feedback, and that version is printed without another review.)

## If something goes wrong
- **`❌ ANTHROPIC_API_KEY is not set`** → set the key in this terminal.
- **`pydantic_core._pydantic_core.ValidationError`** → the critic's answer didn't fit the form (rare). Run it again. If you changed `Review`, check the field types.
- **It always stops after round 1 with a high score** → the critic is too generous. Make `CRITIC` stricter (exercise 1).
- **It takes a while** → each round is 2 requests to Claude (review + rewrite), so 3 rounds is up to 6 requests. `CLAUDE_MODEL=claude-haiku-5-5` is faster and cheaper.

## Try this
1. Make the critic much harsher (e.g. add `"Scores above 6 are very rare."` to `CRITIC`), then much nicer. How does the number of rounds change?
   <details><summary>Hint</summary>

   A harsh critic usually uses all 3 rounds and the final draft may still score under 8. A kind one often gives 8+ straight away, so nothing improves. The critic's instructions control the quality bar, so they deserve as much care as the writer's.
   </details>
2. Make the critic also return `strength`: one sentence about the draft's best point, and print it each round.
   <details><summary>Solution</summary>

   Add a field to the form, and print it:
   ```python
   class Review(BaseModel):
       score: int
       feedback: list[str]
       strength: str                 # one sentence: the best thing about this draft
   ```
   ```python
   print(f"\n--- Round {round_number}: score {review.score}/10 ---")
   print(f"   👍 {review.strength}")
   ```
   No prompt change is needed: the form's field names are sent to Claude, and `strength` is a clear enough name. (The `#` comment is only for you; Claude never sees it.)
   </details>
3. Turn it into a "coder and tester" team: the writer writes a Python function, the critic checks it for bugs and edge cases.
   <details><summary>Hint</summary>

   Change the two roles and the default task, for example:
   ```python
   WRITER = "You are a careful Python developer. Output only the code of the function, with a docstring."
   CRITIC = ("You are a strict code reviewer. Score from 1 to 10. List 2-4 specific bugs, missing edge cases "
             "(empty input, negative numbers...) or unclear names.")
   task = "A Python function is_palindrome(text) that ignores spaces, punctuation and upper/lower case."
   ```
   The loop doesn't change at all: that's the power of a general pattern.
   </details>

## Check yourself
1. The writer and critic are the same model. What makes them behave differently?
2. Why does the critic use `ask_for_data` with a `Review` form instead of `ask`?
3. What two things can end the loop?
4. Why is reviewing by a second AI often better than asking one AI to "write it well the first time"?

<details><summary>Answers</summary>

1. Their system prompts (`WRITER` and `CRITIC`): different instructions give different roles and standards.
2. So the code gets a real number for `score` and a list for `feedback`. With free text, you'd have to dig the score out of a paragraph, which can break.
3. A score of 8 or more (`break`), or reaching 3 rounds.
4. The critic looks at the draft from the outside with one job, finding problems, and gives specific feedback. The writer then fixes concrete issues instead of guessing what "better" means.
</details>

## Learn more (optional)
- [Anthropic: Building effective agents](https://www.anthropic.com/engineering/building-effective-agents) (see "evaluator-optimizer")
- [Claude docs: structured outputs](https://platform.claude.com/docs/en/build-with-claude/structured-outputs)

## Next
→ [30 · AI customer-support team](../30-ai-customer-support-team)
