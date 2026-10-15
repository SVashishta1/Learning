"""Project 8.3: a research TEAM working in parallel (the orchestrator-workers pattern).

  Planner splits the topic into sub-questions  ->  N Researchers search the web IN PARALLEL
  ->  Writer combines their notes into a cited report  ->  Fact-checker flags unsupported claims  ->  Writer fixes them

python research_team.py "Which small open-source LLMs run well on a laptop in 2026, and what are they good at?"
"""
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field

import llm
from agent_core import Agent, cost_report


def web_search_tool(model: str) -> dict:
    """Claude's built-in web search (a SERVER tool). Opus/Sonnet get the newest version; Haiku uses the basic one."""
    version = "web_search_20250305" if "haiku" in model else "web_search_20260209"
    return {"type": version, "name": "web_search", "max_uses": 4}       # max_uses caps searches (and cost) per researcher


class Plan(BaseModel):
    sub_questions: list[str] = Field(description="3 to 5 specific, non-overlapping questions that together answer the topic")
    audience: str = Field(description="Who the final report is for")


class FactCheck(BaseModel):
    unsupported_claims: list[str] = Field(description="Claims in the report NOT backed by the research notes")
    missing_citations: list[str] = Field(description="Sentences stating facts without a [n] citation")
    verdict: Literal["pass", "needs_fixes"]


def make_team(client=None, verbose=True):
    common = {"client": client, "verbose": verbose}
    planner = Agent("Planner", "You plan research. Break topics into precise, searchable sub-questions.", effort="low", **common)
    writer = Agent("Writer", ("You write clear research briefs in Markdown: a 3-sentence summary, then sections, then a numbered "
                              "Sources list. Every factual sentence must cite sources like [1]. Use ONLY the research notes given."), **common)
    checker = Agent("FactChecker", "You verify reports against research notes. Be strict and specific.", effort="low", **common)
    return planner, writer, checker


def research(question: str, n: int, client=None, verbose=True) -> tuple[str, Agent]:
    agent = Agent(f"Researcher-{n}", ("You are a meticulous researcher. Search the web, prefer primary and recent sources, "
                                      "and return concise bullet-point notes. Put the source URL after each bullet."),
                  server_tools=[web_search_tool(llm.MODEL)], client=client, verbose=verbose, max_steps=6, effort="low")
    return agent.run(question), agent


def run(topic: str, client=None, verbose=True) -> tuple[str, list[Agent]]:
    planner, writer, checker = make_team(client, verbose)
    plan = planner.ask_structured(f"Topic: {topic}", Plan)
    questions = plan.sub_questions[:5] or [topic]       # never more than 5 researchers, never zero

    # Workers run at the same time: 4 researchers take ~ as long as 1
    with ThreadPoolExecutor(max_workers=len(questions)) as pool:
        futures = [pool.submit(research, q, i + 1, client, verbose) for i, q in enumerate(questions)]
        results = [f.result() for f in futures]
    notes = "\n\n".join(f"## {q}\n{text}" for q, (text, _) in zip(questions, results))

    report = writer.run(f"Topic: {topic}\nAudience: {plan.audience}\n\n<research_notes>\n{notes}\n</research_notes>\n\nWrite the report.")
    check = checker.ask_structured(f"<research_notes>\n{notes}\n</research_notes>\n\n<report>\n{report}\n</report>", FactCheck)
    if check.verdict != "pass" and (check.unsupported_claims or check.missing_citations):
        report = writer.run(f"<research_notes>\n{notes}\n</research_notes>\n\n<report>\n{report}\n</report>\n\n"
                            "Fix these problems (remove or correctly cite each one), keep everything else:\n"
                            + "\n".join(f"- {c}" for c in check.unsupported_claims + check.missing_citations))
    return report, [planner, *[a for _, a in results], writer, checker]


if __name__ == "__main__":
    topic = " ".join(sys.argv[1:]) or "What are the most in-demand skills for AI engineers in 2026, and how can a beginner learn them?"
    report, agents = run(topic)
    Path("report.md").write_text(f"# {topic}\n\n{report}\n", encoding="utf-8")
    print("\n" + report + "\n\nSaved report.md\n")
    print(cost_report(agents))
