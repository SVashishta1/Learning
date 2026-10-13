# An AI RESEARCH TEAM: a planner splits the topic into questions, several researchers search the web
# AT THE SAME TIME, and a writer turns their notes into a report with sources.
import sys
from concurrent.futures import ThreadPoolExecutor

from pydantic import BaseModel

import ai
from agent import run_agent


class Plan(BaseModel):
    questions: list[str]          # 3 focused questions to research


topic = " ".join(sys.argv[1:]) or "What skills do junior AI engineers need in 2026, and how can a beginner learn them for free?"

# 1. PLANNER
plan = ai.ask_for_data(f"Topic: {topic}\nSplit it into exactly 3 focused research questions.", Plan,
                       system="You are a research planner.")
print("🗺️  Plan:")
for q in plan.questions:
    print(f"   • {q}")


# 2. RESEARCHERS, all working at the same time
def research(question):
    return run_agent(question, web_search=True, name="Researcher", show=False,
                     system="You are a researcher. Search the web and return 5 short bullet-point facts, each with its source link.")


print("\n🔎 Researching all questions at the same time...")
with ThreadPoolExecutor() as pool:
    notes = list(pool.map(research, plan.questions))
all_notes = "\n\n".join(f"## {q}\n{n}" for q, n in zip(plan.questions, notes))

# 3. WRITER
report = ai.ask(f"Topic: {topic}\n\nResearch notes:\n{all_notes}\n\nWrite the report.", max_tokens=4000,
                system="You write clear, friendly reports for beginners: a short summary, then sections, then a list of sources. "
                       "Use only facts from the notes.")
with open("report.md", "w") as f:
    f.write(report)
print(f"\n{report}\n\n📄 Saved to report.md")
