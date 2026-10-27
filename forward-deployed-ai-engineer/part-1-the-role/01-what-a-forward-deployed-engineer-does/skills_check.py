# skills_check.py: rate yourself on the 12 skills a forward deployed AI engineer uses,
# then get a personal study plan that points to the exact courses in this repo.
#
#   python skills_check.py                          (asks you 12 questions)
#   python skills_check.py --answers 3,2,1,0,...    (12 numbers, no questions asked)
import argparse

# Each skill: (name, what it means in plain words, where this repo teaches it).
# The order is the order you should learn them in: earlier skills support later ones.
SKILLS = [
    ("Python and APIs", "write small programs, build and call web APIs",
     "ai-from-zero/part-1-apis, ai-engineer-journey/level-1-apis"),
    ("Machine learning basics", "know what training, a model and an evaluation are",
     "ai-from-zero/part-2-machine-learning, ai-from-zero/part-3-neural-networks"),
    ("LLM apps", "chatbots, RAG over documents, agents with tools",
     "ai-from-zero/part-4-chatbots to part-6-ai-agents-and-teams, ai-engineer-journey/level-7 and level-8"),
    ("How LLMs work inside", "tokens, attention, training, fine-tuning",
     "llm-from-scratch (deep), ai-engineer-journey/level-5 and level-6 (lighter)"),
    ("Linux and the terminal", "move around, read logs, write scripts, run servers",
     "linux-from-zero"),
    ("Git, Docker and CI", "save points, containers, automatic tests on every change",
     "cloud-and-devops-for-ai (Git and Docker sections)"),
    ("Kubernetes and cloud", "run services at scale in AWS, GCP or Azure",
     "cloud-and-devops-for-ai (Kubernetes and cloud sections)"),
    ("Open and local models", "Ollama, llama.cpp, vLLM, models that run with no internet",
     "open-source-and-on-device-ai"),
    ("Customer skills", "discovery, scoping, design docs, demos, clear writing",
     "forward-deployed-ai-engineer/part-1-the-role"),
    ("Enterprise data and integration", "SQL, messy files, company APIs, SSO, private data",
     "forward-deployed-ai-engineer/part-2-enterprise-data-and-integration"),
    ("Production LLM engineering", "evals, guardrails, cost, tracing",
     "forward-deployed-ai-engineer/part-3-production-llm-engineering"),
    ("Agents and deployment at the customer", "agent teams, approvals, VPC and air-gapped installs",
     "forward-deployed-ai-engineer/part-4-agents-at-work, part-5-deploying-at-the-customer"),
]

LEVELS = {0: "never heard of it", 1: "heard of it / followed a tutorial",
          2: "built something with it", 3: "could teach it"}


def parse_answers(text):
    """Turn '3,2,1,...' into a list of 12 whole numbers between 0 and 3, or explain what is wrong."""
    parts = [p.strip() for p in text.split(",") if p.strip()]
    if len(parts) != len(SKILLS):
        raise ValueError(f"Give exactly {len(SKILLS)} numbers, one per skill (you gave {len(parts)}).")
    scores = []
    for p in parts:
        if p not in {"0", "1", "2", "3"}:
            raise ValueError(f"Each answer must be 0, 1, 2 or 3 (got {p!r}).")
        scores.append(int(p))
    return scores


def ask_scores():
    """Ask one question per skill in the terminal."""
    print("Rate yourself from 0 to 3 for each skill:")
    for number, meaning in LEVELS.items():
        print(f"  {number} = {meaning}")
    scores = []
    for name, meaning, _ in SKILLS:
        while True:
            answer = input(f"\n{name} ({meaning}): ").strip()
            if answer in {"0", "1", "2", "3"}:
                scores.append(int(answer))
                break
            print("  Please type 0, 1, 2 or 3.")
    return scores


def study_plan(scores):
    """The skills you rated below 2, kept in learning order. Those are your next steps."""
    return [(name, where, score) for (name, _, where), score in zip(SKILLS, scores) if score < 2]


def report(scores):
    """Build the text report: a little bar chart, then the plan."""
    lines = ["", "Your skills profile", "-" * 19]
    for (name, _, _), score in zip(SKILLS, scores):
        bar = "#" * (score * 4) + "." * ((3 - score) * 4)             # 12 characters wide: full bar = 3
        lines.append(f"{name:<40} [{bar}] {score}/3")
    total = sum(scores)
    lines.append(f"\nTotal: {total}/{3 * len(SKILLS)} ({round(100 * total / (3 * len(SKILLS)))}% of the way)")
    plan = study_plan(scores)
    if not plan:
        lines.append("\nEvery skill is at 2 or more. Go straight to the capstones in Part 6, then Part 7 (career).")
        return "\n".join(lines)
    lines.append("\nYour study plan (in this order):")
    for step, (name, where, score) in enumerate(plan, start=1):
        lines.append(f"  {step}. {name} (now {score}/3) -> {where}")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Rate your FDE skills and get a study plan.")
    parser.add_argument("--answers", help="12 comma-separated numbers 0-3, e.g. 3,2,1,0,0,1,0,0,1,0,0,0")
    args = parser.parse_args()
    try:
        scores = parse_answers(args.answers) if args.answers else ask_scores()
    except ValueError as problem:
        raise SystemExit(f"Problem: {problem}")
    except (KeyboardInterrupt, EOFError):
        raise SystemExit("\nStopped. Run it again any time.")
    print(report(scores))


if __name__ == "__main__":
    main()
