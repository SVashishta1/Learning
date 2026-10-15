import json

import server


def test_add_search_quiz_and_record(tmp_path, monkeypatch):
    monkeypatch.setattr(server, "NOTES_FILE", tmp_path / "notes.json")
    server.add_note("RAG", "What does RAG retrieve?", "Relevant chunks")
    assert "Relevant chunks" in server.search_notes("rag")
    card = json.loads(server.quiz_me("RAG"))
    assert card["question"] == "What does RAG retrieve?"
    assert "1 right" in server.record_result(card["id"], True)
    assert json.loads(server.topics()) == {"RAG": 1}


def test_empty_quiz_and_prompt_template(tmp_path, monkeypatch):
    monkeypatch.setattr(server, "NOTES_FILE", tmp_path / "notes.json")
    assert "No notes yet" in server.quiz_me()
    assert "No note 99" == server.record_result(99, True)
    assert "record_result" in server.study_session("RAG")        # the prompt tells the AI how to run a session
