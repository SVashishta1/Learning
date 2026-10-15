import json

import pytest

import organizer as org
from make_messy_folder import build


@pytest.fixture(autouse=True)
def sandbox(tmp_path, monkeypatch):
    monkeypatch.setattr(org, "SANDBOX", tmp_path)
    monkeypatch.setattr(org, "AUDIT_LOG", tmp_path / "audit.jsonl")
    monkeypatch.setattr(org, "DRY_RUN", False)
    build(tmp_path / "downloads")


def test_sandbox_blocks_escape():
    with pytest.raises(PermissionError):
        org.safe_path("../../etc/passwd")


def test_move_and_delete_are_audited_and_reversible(tmp_path):
    assert "Moved" in org.move_file("downloads/song.mp3", "downloads/Music/song.mp3")
    assert (tmp_path / "downloads/Music/song.mp3").exists()
    assert "recoverable" in org.delete_file("downloads/untitled.txt")
    assert any((tmp_path / ".trash").iterdir())
    actions = [json.loads(line)["action"] for line in (tmp_path / "audit.jsonl").read_text(encoding="utf-8").splitlines()]
    assert actions == ["move", "delete"]


def test_dry_run_changes_nothing(tmp_path, monkeypatch):
    monkeypatch.setattr(org, "DRY_RUN", True)
    assert "would move" in org.move_file("downloads/song.mp3", "downloads/Music/song.mp3")
    assert (tmp_path / "downloads/song.mp3").exists()


def test_list_shows_duplicate_hashes():
    listing = org.list_files("downloads")
    h1 = [l for l in listing.splitlines() if "invoice_october.pdf" in l][0].split("md5 ")[1]
    h2 = [l for l in listing.splitlines() if "Invoice_October (1).pdf" in l][0].split("md5 ")[1]
    assert h1 == h2


def test_declined_actions_are_audited(tmp_path, monkeypatch):
    monkeypatch.setattr(org, "cli_approver", lambda *args: False)       # the human says no
    assert org.approver("Organizer", "delete_file", {"path": "downloads/song.mp3"}) is False
    entry = json.loads((tmp_path / "audit.jsonl").read_text(encoding="utf-8").splitlines()[-1])
    assert entry["action"] == "declined" and entry["path"] == "downloads/song.mp3"
