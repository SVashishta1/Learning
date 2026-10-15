# Part 6 · AI agents & teams

**An agent is an AI that can DO things, not just talk.** You give it **tools** (your Python functions: a calculator, a weather lookup, a database...). It decides which tool to use, looks at the result, and keeps going until the job is done.
**A team (multi-agent system)** is several agents with different jobs working together: one writes and one checks, or one receptionist routes work to specialists.

```
your task ──► AI ──"use calculate(17*3.45)"──► your Python runs it ──► result back to the AI ──► ... ──► final answer
```

| # | Project | What you'll have |
|---|---------|------------------|
| 27 | [AI uses a calculator](27-ai-uses-a-calculator) | your first agent, with the loop written out in full |
| 28 | [Agent with many tools](28-agent-with-many-tools) | weather, time, web search, saving notes |
| 29 | [Two AIs: writer and critic](29-two-ais-writer-and-critic) | one AI writes, one grades, until it's good |
| 30 | [AI customer-support team](30-ai-customer-support-team) | a receptionist AI routes to specialist AIs; refunds need your OK |
| 31 | [AI research team](31-ai-research-team) | AIs research the web at the same time and write a report |
| 32 | [Final project: your personal AI assistant](32-final-project-your-personal-ai-assistant) | a web app with a team of agents: your documents, the web, your to-do list |

**Time:** about 1–2 weeks at 1 hour a day.

## Install once
With your virtual environment switched on (see [00 · Start here](../00-start-here)):
```bash
pip install anthropic chromadb pypdf fastapi "uvicorn[standard]" python-multipart httpx tzdata
```
- `anthropic`: talks to Claude
- `chromadb`, `pypdf`: the vector database and PDF reader from Part 5 (project 32)
- `fastapi`, `uvicorn[standard]`, `python-multipart`: the web app and its file uploads (project 32)
- `httpx`: calls the free weather service (project 28)
- `tzdata`: the world's time zones (project 28; Windows needs it, on Mac it does no harm)

Every project here uses Claude, so you need your API key: see the [Part 4 README](../part-4-chatbots), step "Get your API key". While learning, `CLAUDE_MODEL=claude-haiku-5-5` makes everything much cheaper.

From project 28 on, every project uses **`agent.py`**, a ~60-line agent engine. Project 27 shows you exactly what's inside it.

## Next
Project 32 is the course finale. When you've built it, continue with [Voice AI from Zero](../../voice-ai-from-zero) or the deeper [AI Engineer Journey](../../ai-engineer-journey).
