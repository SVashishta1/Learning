# 27 · AI uses a calculator

**What it does:** your first **agent**. Claude gets a calculator tool you wrote, decides by itself when to use it, reads the results, and gives a final answer.

## Run it
```bash
cd part-6-ai-agents-and-teams/27-ai-uses-a-calculator
python calculator_agent.py
python calculator_agent.py "If I save $250 a month at 0 interest, how many months until I have $7000?"
```
You'll see each tool use (🔧) before the final answer.

## The idea in one sentence
The AI can't run code itself, so it **asks** to use a tool, **your** code runs it, you send the result back, and the AI continues. That loop (ask → tool → result → ask again) is what every AI agent is.

## Try this
1. Add a second tool, `square_root(number)`. Write the function, describe it, and add it to `tools=[...]`.
2. Remove the calculator from `tools=[...]` and ask a hard sum. Does the AI get it right without it?
