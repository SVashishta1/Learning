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
