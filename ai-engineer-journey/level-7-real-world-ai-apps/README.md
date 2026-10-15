# Level 7 · Real-world AI apps: putting it all together

Now you combine everything: APIs (Level 1), embeddings (5.4) and an LLM, into the kind of products companies are hiring AI engineers to build *right now*.

| # | Project | What you'll be able to say in an interview |
|---|---------|---------------------------------------------|
| 7.1 | [Chatbot API with memory](01-chatbot-api-with-memory-in-a-database) | "I built a streaming chat API with persistent conversation memory" |
| 7.2 | [Structured data extractor](02-structured-data-extractor-invoices-to-json) | "I turn messy documents into validated JSON with schema-constrained outputs" |
| 7.3 | [RAG: ask your PDFs](03-rag-ask-questions-about-your-pdfs) | "I built retrieval-augmented generation with chunking, embeddings, a vector index and cited answers" |
| 7.4 | [AI agent with tools](04-ai-agent-with-tools-calculator-weather-search) | "I implemented the agent loop: tool schemas, tool execution, web search, step limits" |
| 7.5 | [Evaluate it](05-evaluate-your-rag-and-chatbot) | "I measure quality with a test set, retrieval metrics, LLM-as-judge, latency and cost" |
| 7.6 | [Capstone: deploy a full AI app](06-capstone-deploy-a-full-ai-app) | "I shipped it: Docker, auth, rate limiting, logging, metrics, CI" |

## API key (needed from here on)
These projects call **Claude** through the official Anthropic SDK.
1. Create a key in the Claude Console: https://platform.claude.com (add a few dollars of credit; these projects cost cents).
2. Set it in your terminal (never commit it!):
   ```bash
   export ANTHROPIC_API_KEY=sk-ant-...          # macOS/Linux
   $env:ANTHROPIC_API_KEY="sk-ant-..."          # Windows PowerShell
   ```
3. Optional: `export CLAUDE_MODEL=claude-haiku-5-5` for the cheapest, fastest model while experimenting. The default is `claude-opus-5-5`.

Every project has a small `llm.py` helper (same in each folder) and **tests that use a fake LLM**. `pytest` runs free and offline, which is exactly how professionals test LLM apps in CI.

**Read this first (20 min, best free resource on building with LLMs):** Anthropic, "Building effective agents": https://www.anthropic.com/engineering/building-effective-agents

**Start here →** [7.1 · Chatbot API with memory](01-chatbot-api-with-memory-in-a-database)
