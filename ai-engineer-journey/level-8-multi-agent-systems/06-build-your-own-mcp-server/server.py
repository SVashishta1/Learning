"""Project 8.6: an MCP server: a 'USB port' that lets ANY AI app (Claude Code, Claude Desktop, your own agents)
use your tools and data. This one is a study-notes server with flashcard quizzes.

Run standalone (it talks over stdin/stdout, so it waits silently):  python server.py
"""
import json
import random
from datetime import datetime
from pathlib import Path

from mcp.server.mcpserver import MCPServer

NOTES_FILE = Path(__file__).with_name("notes.json")
mcp = MCPServer("study-notes")


def _load() -> list[dict]:
    return json.loads(NOTES_FILE.read_text()) if NOTES_FILE.exists() else []


def _save(notes: list[dict]):
    NOTES_FILE.write_text(json.dumps(notes, indent=2))


@mcp.tool()
def add_note(topic: str, question: str, answer: str) -> str:
    """Save a study note as a question/answer flashcard under a topic (e.g. 'RAG', 'PyTorch')."""
    notes = _load()
    notes.append({"id": len(notes) + 1, "topic": topic, "question": question, "answer": answer,
                  "created": datetime.now().isoformat(timespec="seconds"), "correct": 0, "wrong": 0})
    _save(notes)
    return f"Saved note #{len(notes)} in '{topic}'."


@mcp.tool()
def search_notes(query: str) -> str:
    """Find notes whose topic, question or answer contains the query words."""
    words = query.lower().split()
    hits = [n for n in _load() if any(w in (n["topic"] + n["question"] + n["answer"]).lower() for w in words)]
    return json.dumps(hits[:10], indent=1) if hits else "No matching notes."


@mcp.tool()
def quiz_me(topic: str = "") -> str:
    """Pick a flashcard to quiz the user, favouring cards they got wrong before. Returns the question and the hidden answer."""
    notes = [n for n in _load() if not topic or n["topic"].lower() == topic.lower()]
    if not notes:
        return "No notes yet. Add some with add_note."
    card = random.choices(notes, weights=[1 + 2 * n["wrong"] - 0.5 * min(n["correct"], 1) for n in notes])[0]
    return json.dumps({"id": card["id"], "question": card["question"], "answer_for_grading_only": card["answer"]})


@mcp.tool()
def record_result(note_id: int, was_correct: bool) -> str:
    """Record whether the user answered a quiz card correctly (spaced repetition)."""
    notes = _load()
    for n in notes:
        if n["id"] == note_id:
            n["correct" if was_correct else "wrong"] += 1
            _save(notes)
            return f"Recorded. Card {note_id}: {n['correct']} right / {n['wrong']} wrong."
    return f"No note {note_id}"


@mcp.resource("notes://topics")
def topics() -> str:
    """A read-only overview of topics and card counts."""
    counts: dict[str, int] = {}
    for n in _load():
        counts[n["topic"]] = counts.get(n["topic"], 0) + 1
    return json.dumps(counts)


@mcp.prompt()
def study_session(topic: str) -> str:
    """A ready-made prompt template: run a 5-question quiz on a topic."""
    return (f"Run a 5-question study session on '{topic}'. For each: call quiz_me, ask me the question WITHOUT revealing "
            "the answer, wait for my reply, grade it kindly, call record_result, then continue. Finish with a score.")


if __name__ == "__main__":
    mcp.run()          # stdio transport: the AI app starts this process and talks to it via stdin/stdout
