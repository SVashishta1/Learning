# 28 · Agent with many tools

**What it does:** an assistant with a calculator, live weather, world clocks, a note-saver and **web search**. For each question it chooses which tools to use, and in what order, by itself.

## Run it
```bash
cd part-6-ai-agents-and-teams/28-agent-with-many-tools
pip install httpx
python assistant.py
python assistant.py "What time is it in Tokyo, and how many hours ahead of London is that?"
```
Then open `notes.txt` to see what it saved.

## The idea in one sentence
Each tool is a normal Python function plus a one-line description (`tool(...)`); the agent engine in `agent.py` handles the loop from project 27 for you.

## Try this
1. Write a new tool, e.g. `flip_coin()` or `random_joke()`, and add it to `tools`.
2. Ask something that needs 3 tools at once and watch the order it picks.
3. Make the descriptions vague ("does stuff"). Does the agent still pick the right tools? (Good descriptions matter!)
