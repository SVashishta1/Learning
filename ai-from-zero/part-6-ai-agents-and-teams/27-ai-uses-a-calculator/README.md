# 27 · AI uses a calculator

**What you'll build:** your first **agent**. Claude gets a calculator tool that you wrote, decides by itself when to use it, reads the results, and gives a final answer.
**Time:** ~45 min · **Builds on:** [26 · Production vector database](../../part-5-rag-and-vector-databases/26-production-vector-database-postgres) (end of Part 5) and the `ai.py` helper from [Part 4](../../part-4-chatbots) · **Needs:** an Anthropic API key

## Why this matters
Language models are bad at exact arithmetic and can't look anything up or change anything by themselves. **Tool use** fixes that: the AI asks your code to do the job. Every "AI agent" product (coding assistants, booking assistants, support bots that issue refunds) is this same loop with more tools. Once you understand these 40 lines, agents stop being magic.

## What you'll learn
- **Tool:** a normal Python function that the AI is allowed to ask for.
- **Tool description (schema):** a name, a sentence and a list of inputs that tell the AI what the tool does and how to call it.
- **Tool use:** the AI can't run code; it replies "please run `calculate` with `17 * 3.45`", your code runs it, and you send the result back.
- **The agent loop:** ask → if the AI wants a tool, run it and send the result → ask again → stop when it gives a final answer.
- **`stop_reason`:** the field that tells you whether the AI is finished (`end_turn`) or waiting for a tool (`tool_use`).

## Before you start
- Install the Part 6 packages (once):
  ```bash
  pip install anthropic chromadb pypdf fastapi "uvicorn[standard]" python-multipart httpx tzdata
  ```
  This lesson only needs `anthropic` (talks to Claude).
- Set your API key in this terminal (full steps in the [Part 4 README](../../part-4-chatbots)):
  ```bash
  export ANTHROPIC_API_KEY=sk-ant-your-key-here        # Mac
  $env:ANTHROPIC_API_KEY="sk-ant-your-key-here"        # Windows PowerShell
  ```

## Run it
1. From the course folder (`Learning/ai-from-zero`), with your venv switched on:
   ```bash
   cd part-6-ai-agents-and-teams/27-ai-uses-a-calculator
   python calculator_agent.py
   ```
2. Give it your own problem (in quotes):
   ```bash
   python calculator_agent.py "If I save $250 a month, how many months until I have $7000?"
   ```
   On Mac, use single quotes when your text contains `$`, otherwise the terminal swallows `$250`: `python calculator_agent.py 'If I save $250 a month...'`

### What you should see
```
🔧 the AI used calculate(17 * 3.45 + 4 * 1.20) → 63.45
🔧 the AI used calculate(100 - 63.45) → 36.55

💬 17 notebooks cost $58.65 and 4 pens cost $4.80, so you spend $63.45 in total. From $100 you get **$36.55** in change.
```
Each `🔧` line is one tool use: the AI wrote the expression, **your** function calculated it. The AI may use the tool once or several times, and its final wording will differ, but the numbers in the answer should match the `🔧` results.

## How it works
```
question ──► Claude ──"tool_use: calculate('17 * 3.45 + 4 * 1.20')"──► your calculate() ──► "63.45"
                ▲                                                                            │
                └──────────────── tool_result "63.45" sent back ◄──────────────────────────────┘
          ... repeat until stop_reason is not "tool_use" ──► 💬 final answer
```
1. **The tool.** `calculate(expression)` is plain Python. For safety it first checks that the text only contains digits, spaces and `+ - * / ( ) .`, so the AI can't run other code. `eval(expression)` runs the maths, `round(result, 10)` hides tiny computer rounding errors (like `12.499999999999998` instead of `12.5`), and `try/except` turns errors like dividing by zero into a message the AI can read, instead of crashing your program.
2. **The description.** `calculator_tool` is a dictionary the AI reads: a `name`, a `description` ("Always use this for arithmetic") and an `input_schema`, which says the tool takes one text input called `expression`. Good descriptions are how the AI knows *when* to use a tool.
3. **The question.** `sys.argv[1:]` is what you typed after the file name; if you typed nothing, the notebooks-and-pens question is used. `messages` starts as a one-message conversation.
4. **The loop** (`while True:`):
   - `ai.send(..., tools=[calculator_tool])` sends the conversation plus the list of tools.
   - The reply is added to `messages` (the AI must see its own tool requests next time).
   - If `response.stop_reason != "tool_use"`, the AI is done: print the text blocks and `break`.
   - Otherwise, for each `tool_use` block, call `calculate(**block.input)` (the `**` turns `{"expression": "100 - 63.45"}` into `calculate(expression="100 - 63.45")`), print it, and build a `tool_result` with the same `tool_use_id`, so the AI knows which request each answer belongs to.
   - All results go back as one `user` message, and the loop asks again.

That loop is the whole idea of an agent. From lesson 28 on, the same loop lives in `agent.py` so each project can focus on its tools.

## If something goes wrong
- **`❌ ANTHROPIC_API_KEY is not set`** or **`❌ Your API key is wrong`** → set the key in this terminal (see Before you start). New terminal windows need it again.
- **The answer has no `🔧` lines** → the AI decided it didn't need the tool (easy sums). Try a harder one, like `"What is 48291 * 7703 / 13?"`.
- **Your question lost its dollar amounts** (e.g. "save  a month") → on Mac/Linux, `$250` inside double quotes is treated as a variable. Use single quotes around the question.
- **`anthropic.RateLimitError`** or **`overloaded_error`** → too many requests or Claude is busy. Wait a minute and try again.

## Try this
1. Remove the tool: change `tools=[calculator_tool]` to `tools=[]` and ask `"What is 48291 * 7703 / 13?"`. Is the answer exactly right? (The correct answer is 28614274.846...) Put the tool back afterwards.
   <details><summary>Hint</summary>

   Without a calculator, modern models are often close, but long exact answers can be slightly off, and you can't tell when. With the tool, the maths is done by Python, so it is exact every time. That's the point of tools: let the AI decide *what* to do and let code do the exact work.
   </details>
2. Add a second tool, `square_root(number)`, and ask `"What is the square root of 7 times the square root of 28?"`.
   <details><summary>Solution</summary>

   Add the function and its description next to the calculator:
   ```python
   def square_root(number):
       return str(float(number) ** 0.5)

   root_tool = {
       "name": "square_root",
       "description": "Square root of a number.",
       "input_schema": {"type": "object", "properties": {"number": {"type": "number"}}, "required": ["number"]},
   }
   ```
   Send both tools: `tools=[calculator_tool, root_tool]`. In the loop, call the right function by name:
   ```python
   if block.name == "square_root":
       answer = square_root(**block.input)
   else:
       answer = calculate(**block.input)
   print(f"🔧 the AI used {block.name}({block.input}) → {answer}")
   ```
   (The answer is 14.)
   </details>
3. Make the loop safer: real agents never loop forever. Replace `while True:` so it stops after 5 rounds and prints `Gave up after 5 steps.`.
   <details><summary>Solution</summary>

   ```python
   for step in range(5):
       ... # the same loop body as before
   else:
       print("Gave up after 5 steps.")
   ```
   A `for ... else` runs the `else` part only if the loop finished without `break`. `agent.py` (next lesson) uses the same idea with `max_steps`.
   </details>

## Check yourself
1. Who actually runs the `calculate` function: Claude or your computer?
2. What does `stop_reason == "tool_use"` mean, and what must your code do next?
3. Why does each `tool_result` include the `tool_use_id`?
4. Why does the code check the characters in `expression` before calling `eval`?

<details><summary>Answers</summary>

1. Your computer. Claude only asks for it; your Python code decides whether and how to run it.
2. The AI is waiting for one or more tool results. Your code must run the tools, send the results back, and ask again.
3. The AI can ask for several tools at once; the id tells it which result answers which request.
4. `eval` would run *any* Python code. Allowing only digits and maths symbols stops the AI (or a user tricking it) from running something harmful.
</details>

## Learn more (optional)
- [Claude docs: tool use overview](https://platform.claude.com/docs/en/agents-and-tools/tool-use/overview)
- [Anthropic: Building effective agents](https://www.anthropic.com/engineering/building-effective-agents)
- Video search: [how AI agents use tools](https://www.youtube.com/results?search_query=llm+tool+calling+explained)

## Next
→ [28 · Agent with many tools](../28-agent-with-many-tools)
