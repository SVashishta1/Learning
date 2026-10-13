# 31 · AI research team

**What it does:** give it any topic. A **planner AI** splits it into 3 questions, three **researcher AIs** search the live web *at the same time*, and a **writer AI** combines their notes into a report with sources, saved as `report.md`.

## Run it
```bash
cd part-6-ai-agents-and-teams/31-ai-research-team
python research_team.py
python research_team.py "Which electric cars under $35,000 have the best range in 2026?"
```

## The idea in one sentence
Big jobs go faster when you **split them up**: one AI plans, several work in parallel, and one puts the results together. This is how AI "deep research" features work.

## Try this
1. Ask the planner for 5 questions instead of 3.
2. Add a 4th AI, a "fact checker", that reads the report and lists any claim without a source.
