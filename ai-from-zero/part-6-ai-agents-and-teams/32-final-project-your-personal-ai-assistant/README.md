# 32 · Final project: your personal AI assistant 🎓

**What it does:** a web app run by a **team of AI agents**. A receptionist AI reads each message and hands it to the right specialist:

| Specialist | Uses | Built in |
|-----------|------|----------|
| 📚 **Librarian** | your documents (upload PDFs!) via a **vector database** | Part 5 |
| 🌍 **Researcher** | live **web search** | Part 6 |
| ✅ **Organizer** | your **to-do list** in a database | Part 1 |
| 💬 **Chatter** | friendly conversation, with **memory** | Part 4 |

Each answer shows which specialist replied and which tools it used. Your to-do list updates live on the right.

## Run it
```bash
cd part-6-ai-agents-and-teams/32-final-project-your-personal-ai-assistant
uvicorn app:app --reload
```
Open http://127.0.0.1:8000 and click the three example buttons, then try your own:
- "What's the meal allowance in the expense policy?" → 📚
- "Who won the last Champions League final?" → 🌍
- "Add 'apply to 3 AI internships' to my list" → ✅ then "show my tasks"
- Upload your CV as a PDF and ask "What are my strongest skills according to my CV?" → 📚

## How it all fits together
```
 browser (page.html) ──► app.py (API) ──► assistant.py
                                              ├─ Receptionist (ai.ask_for_data → picks a specialist)
                                              └─ Specialist  (agent.py loop + its own tools)
                                                   ├─ Chroma vector database (your documents)
                                                   ├─ web search
                                                   └─ SQLite to-do database
```
**You understand every piece of this.** That's the point of the whole course.

## Make it yours
1. Add a 5th specialist, e.g. a 🌦️ Weather agent with the `get_weather` tool from project 28.
2. Put your own notes and PDFs in `docs/` so it becomes *your* knowledge assistant.
3. Deploy it with the Dockerfile pattern from project 05, and put the link and a 1-minute demo video on your CV and LinkedIn.

## What next?
You've finished **AI from Zero**! 🎉 For deeper versions of everything (evaluating AI quality, monitoring, MCP servers, fine-tuning, building GPT from scratch), continue with [`../../../ai-engineer-journey`](../../../ai-engineer-journey).
