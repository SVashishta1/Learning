from pathlib import Path

import pytest

import llm
import notes_to_spec
from discovery_check import REQUIRED, check, follow_up_email
from fake_llm import FakeClaude, FakeOllama

HERE = Path(__file__).parent


def test_template_has_every_section_and_all_are_empty():
    answered, missing, _, extra = check((HERE / "notes_template.md").read_text())
    assert answered == [] and missing == list(REQUIRED) and extra == []


def test_northwind_notes_answer_every_section_but_have_open_items():
    answered, missing, open_items, _ = check((HERE / "northwind_interview_notes.md").read_text())
    assert missing == [] and len(answered) == len(REQUIRED)
    assert len(open_items) == 2                      # the two TBDs: hosting option and scanned PDFs


def test_missing_section_turns_into_a_follow_up_question():
    notes = "# Discovery notes: Acme · today\n## Who we talked to\n- Jo, ops lead\n## Data sources\n- TBD\n"
    _, missing, open_items, _ = check(notes)
    assert "Data sources" in missing                 # a bare 'TBD' does not count as an answer
    email = follow_up_email(notes, missing, open_items)
    assert "Hi Acme team" in email
    assert REQUIRED["Data sources"] in email


def make_spec():
    return notes_to_spec.ProblemSpec(
        customer="Northwind Logistics", problem_statement="Agents answer WISMO emails slowly.",
        requested_solution="An AI chatbot", real_need="Faster drafted replies", users="45 agents",
        current_process=["Read email", "Search TMS"],
        pain_points=[notes_to_spec.PainPoint(pain="Slow replies", evidence="FRT 19 h (HelpDesk report)")],
        data_sources=["TMS replica"], systems=["HelpDesk"], constraints=["12-week pilot"],
        success_metrics=[notes_to_spec.Metric(name="FRT", baseline="19 h", target=None)],
        open_questions=["Hosting?"], risks=["Firewall delay"])


def test_claude_path_sends_notes_and_renders_markdown(monkeypatch):
    fake = FakeClaude(parsed=make_spec())
    monkeypatch.setattr(llm, "PROVIDER", "anthropic")
    monkeypatch.setattr(llm, "_client", fake)
    spec = llm.ask_json(notes_to_spec.build_prompt("NOTES HERE"), notes_to_spec.ProblemSpec,
                        system=notes_to_spec.SYSTEM)
    sent = fake.calls[0]
    assert "NOTES HERE" in sent["messages"][0]["content"]
    assert sent["output_format"] is notes_to_spec.ProblemSpec and sent["fallbacks"] == "default"
    markdown = notes_to_spec.to_markdown(spec)
    assert "| FRT | 19 h | unknown |" in markdown and "1. Read email" in markdown


def test_ollama_path_parses_json_even_inside_code_fences(monkeypatch):
    fake = FakeOllama(text="Sure!\n```json\n" + make_spec().model_dump_json() + "\n```")
    monkeypatch.setattr(llm, "PROVIDER", "ollama")
    monkeypatch.setattr(llm, "_client", fake)
    spec = llm.ask_json("notes", notes_to_spec.ProblemSpec)
    assert spec.customer == "Northwind Logistics"
    assert fake.calls[0]["response_format"]["type"] == "json_schema"


def test_missing_key_gives_a_clear_message(monkeypatch):
    monkeypatch.setattr(llm, "PROVIDER", "anthropic")
    monkeypatch.setattr(llm, "_client", None)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    with pytest.raises(SystemExit, match="ANTHROPIC_API_KEY"):
        llm.ask("hi")
