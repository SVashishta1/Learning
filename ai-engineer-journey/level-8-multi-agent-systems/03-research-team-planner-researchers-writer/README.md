# 8.3 · Research team: planner, parallel researchers, writer, fact-checker

**What you build:** a team that researches any topic on the live web and writes a **cited report**:
1. a **Planner** splits the topic into 3–5 sub-questions (structured output),
2. **Researchers run in parallel**, each using Claude's built-in **web search**,
3. a **Writer** combines their notes into a Markdown brief with numbered citations,
4. a **Fact-checker** flags claims the notes don't support, and the Writer fixes them.

**Like you're 10:** a school project. The team captain splits the topic ("you do history, you do science, you do pictures"), everyone researches *at the same time*, one person writes the poster, and the strictest friend checks that every fact has a source before it goes on the wall.

## Run it
```bash
cd level-8-multi-agent-systems/03-research-team-planner-researchers-writer
pip install -r requirements.txt
export ANTHROPIC_API_KEY=sk-ant-...
python research_team.py
python research_team.py "Compare vector databases (pgvector, Chroma, Pinecone) for a startup's RAG app"
```
The output goes to `report.md`, followed by a per-agent cost report.

Tests (offline, with a fake that answers differently per agent): `pytest -v`

## Key ideas
- **Orchestrator-workers:** one planner, many independent workers, then synthesis. Anthropic's own Research feature uses this architecture.
- **Parallelism:** `ThreadPoolExecutor` runs researchers at the same time. It's faster in wall-clock time, but tokens (and cost) add up per agent. Check the cost report!
- **Context isolation:** each researcher has its own short conversation. The writer only sees distilled notes, not 20 pages of raw search results, which keeps quality high and cost down.
- **Verification step:** a separate checker catches hallucinated or uncited claims before a human reads them.

## Your turn
1. Let the Planner choose how many researchers to spawn based on topic complexity (1 for simple, 5 for broad).
2. Give researchers `web_fetch` too (`{"type": "web_fetch_20260209", "name": "web_fetch"}`) so they can read full pages.
3. Add a final "Editor" agent that rewrites the report for a 12-year-old. Compare the two versions.

## Read
- How we built our multi-agent research system (Anthropic): https://www.anthropic.com/engineering/multi-agent-research-system
- Tool use (incl. web search): https://platform.claude.com/docs/en/agents-and-tools/tool-use/overview
