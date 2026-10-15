# Level 8 · Multi-agent systems: AI teams that get real work done

One agent with tools (7.4) is powerful. Real products increasingly use **several specialised agents** that plan, route, check each other and hand work over, with **humans approving** risky steps. These are the patterns companies are hiring for.

All projects share `agent_core.py`, a ~120-line toolkit you can read in 10 minutes (Agent loop, Tool, human approval, structured outputs, cost tracking). Understanding it means you understand what LangGraph, CrewAI and agent SDKs do under the hood.

| # | Project | Pattern | Industry use |
|---|---------|---------|--------------|
| 8.1 | [Writer + critic](01-writer-and-critic-reflection-loop) | reflection / evaluator-optimizer | content, code generation, marketing |
| 8.2 | [Customer-support triage](02-customer-support-router-and-specialists) | router + specialists + handoffs | support automation (very high demand) |
| 8.3 | [Research team](03-research-team-planner-researchers-writer) | orchestrator-workers, parallel agents | analyst reports, due diligence |
| 8.4 | [Data analyst (text-to-SQL)](04-data-analyst-agent-text-to-sql) | agent + guardian reviewer | BI, analytics copilots |
| 8.5 | [Code review crew](05-code-review-crew-parallel-reviewers) | parallel specialists + aggregator | developer tools, security |
| 8.6 | [Build an MCP server](06-build-your-own-mcp-server) | Model Context Protocol | connecting AI to company systems |
| 8.7 | [Human-in-the-loop agent](07-human-in-the-loop-file-organizer-agent) | approvals, sandboxing, audit logs | any agent that takes real actions |
| 8.8 | [Capstone: incident responder](08-capstone-ai-incident-response-team) | full multi-agent workflow | DevOps / SRE automation |

**Setup:** same as Level 7 (`ANTHROPIC_API_KEY`). Tip: `export CLAUDE_MODEL=claude-haiku-5-5` makes multi-agent runs very cheap while you learn. You can also mix models inside one team: `Agent(..., model="claude-haiku-5-5")` gives just that agent a cheaper model, and the cost report prices each agent separately.

Every project has offline tests (`pytest -v`) that use a fake LLM, so you can check your setup and your changes without spending anything.

**Key reading:** Anthropic, "Building effective agents" (workflows vs. agents, the five patterns used in this level): https://www.anthropic.com/engineering/building-effective-agents
And "How we built our multi-agent research system": https://www.anthropic.com/engineering/multi-agent-research-system

**Start here →** [8.1 · Writer + critic](01-writer-and-critic-reflection-loop)
