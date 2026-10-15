"""Project 8.1: two agents improve each other's work (the "reflection" / evaluator-optimizer pattern).

  Writer drafts  ->  Critic scores (structured, 1-10, with concrete fixes)  ->  Writer revises  ->  ... until score >= 8

python writer_critic.py
python writer_critic.py "a cover letter for a junior AI engineer role at a robotics startup, mentioning my FastAPI + RAG projects"
"""
import sys
from pathlib import Path

from pydantic import BaseModel, Field

from agent_core import Agent, cost_report


class Critique(BaseModel):
    score: int = Field(description="Overall quality from 1 (bad) to 10 (excellent, ready to publish)")
    strengths: list[str] = Field(description="What works well (max 3)")
    fixes: list[str] = Field(description="Specific, actionable changes, most important first (max 5)")
    ready: bool = Field(description="True only if this could be published as-is")


WRITER = Agent("Writer", system=("You are an excellent writer. Write clearly, concretely, with no clichés or filler. "
                                  "When given feedback, apply EVERY fix while keeping what works. Output only the text itself."),
               effort="medium")
CRITIC = Agent("Critic", system=("You are a demanding but fair editor. Judge against the brief: is it specific, accurate, "
                                  "well structured, the right length and tone? Give fixes a writer can apply immediately. "
                                  "Reserve 9-10 for genuinely excellent work."),
               effort="medium")


def write_with_feedback(brief: str, target: int = 8, max_rounds: int = 3) -> tuple[str, list[dict]]:
    draft = WRITER.run(f"Write this: {brief}")
    history = []
    for round_no in range(1, max_rounds + 1):
        c = CRITIC.ask_structured(f"<brief>{brief}</brief>\n\n<draft>\n{draft}\n</draft>\n\nCritique this draft.", Critique)
        history.append({"round": round_no, "score": c.score, "fixes": c.fixes})
        print(f"\n📝 Round {round_no}: score {c.score}/10" + "".join(f"\n   - {f}" for f in c.fixes))
        if c.score >= target or c.ready:
            break
        draft = WRITER.run(f"<brief>{brief}</brief>\n\n<previous_draft>\n{draft}\n</previous_draft>\n\n"
                           "Rewrite the draft applying these fixes:\n" + "\n".join(f"- {f}" for f in c.fixes))
    return draft, history


if __name__ == "__main__":
    brief = " ".join(sys.argv[1:]) or ("a 120-word LinkedIn post announcing that I finished building a RAG app that answers "
                                       "questions about a company handbook with citations, aimed at recruiters, no hashtag spam")
    final, history = write_with_feedback(brief)
    print("\n" + "=" * 60 + "\nFINAL\n" + "=" * 60 + "\n" + final)
    Path("output.md").write_text(f"# Brief\n{brief}\n\n# Scores\n{[h['score'] for h in history]}\n\n# Final\n{final}\n", encoding="utf-8")
    print("\n" + cost_report([WRITER, CRITIC]))
