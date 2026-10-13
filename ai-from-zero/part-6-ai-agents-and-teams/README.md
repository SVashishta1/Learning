# Part 6 · AI agents & teams

**An agent is an AI that can DO things, not just talk.** You give it **tools** (your Python functions: a calculator, a weather lookup, a database...). It decides which tool to use, looks at the result, and keeps going until the job is done.
**A team (multi-agent system)** is several agents with different jobs working together: one writes and one checks, or one receptionist routes work to specialists.

| # | Project | What you'll have |
|---|---------|------------------|
| 27 | [AI uses a calculator](27-ai-uses-a-calculator) | your first agent, with the loop written out in full |
| 28 | [Agent with many tools](28-agent-with-many-tools) | weather, time, web search, saving notes |
| 29 | [Two AIs: writer and critic](29-two-ais-writer-and-critic) | one AI writes, one grades, until it's good |
| 30 | [AI customer-support team](30-ai-customer-support-team) | a receptionist AI routes to specialist AIs; refunds need your OK |
| 31 | [AI research team](31-ai-research-team) | AIs research the web at the same time and write a report |
| 32 | [Final project: your personal AI assistant](32-final-project-your-personal-ai-assistant) | a web app with a team of agents: your documents, the web, your to-do list |

Install once: `pip install anthropic chromadb pypdf fastapi "uvicorn[standard]"`. You'll need your API key from Part 4.

From project 28 on, every project uses **`agent.py`**, a ~50-line agent engine. Project 27 shows you exactly what's inside it.
