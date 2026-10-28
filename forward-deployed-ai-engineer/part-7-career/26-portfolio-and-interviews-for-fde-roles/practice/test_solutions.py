import pytest

from solutions import TemporaryError, chunk, fetch_all, merge_contacts


def test_merge_contacts_transitively_and_in_order():
    rows = [{"name": "Ann  Lee", "email": "ANN@x.com ", "phone": ""},
            {"name": "Bob", "email": "bob@y.com", "phone": "+31 (0)6 1234-5678"},
            {"name": "Ann Lee-Smith", "email": "", "phone": "0612345678"},
            {"name": "A. Lee", "email": "ann@x.com", "phone": "06 12 34 56 78"},
            {"name": "Robert", "email": "", "phone": "+31612345678"}]
    out = merge_contacts(rows)
    assert out == [{"name": "Ann Lee-Smith", "email": "ann@x.com", "phone": "0612345678", "sources": 3},
                   {"name": "Robert", "email": "bob@y.com", "phone": "+31612345678", "sources": 2}]


def test_fetch_all_retries_then_succeeds_and_stops_on_loops():
    pages = {None: {"items": [1, 2], "next": "a"}, "a": {"items": [3], "next": None}}
    failures = {"a": 2}
    waits = []

    def get_page(cursor):
        if failures.get(cursor, 0):
            failures[cursor] -= 1
            raise TemporaryError("503")
        return pages[cursor]
    assert fetch_all(get_page, sleep=waits.append) == [1, 2, 3] and waits == [1, 2]

    with pytest.raises(TemporaryError):
        fetch_all(lambda c: (_ for _ in ()).throw(TemporaryError("down")), max_retries=2, sleep=lambda s: None)
    with pytest.raises(PermissionError):
        fetch_all(lambda c: (_ for _ in ()).throw(PermissionError("401")), sleep=lambda s: None)
    loop = {None: {"items": [1], "next": "x"}, "x": {"items": [2], "next": "x"}}
    with pytest.raises(ValueError, match="twice"):
        fetch_all(lambda c: loop[c], sleep=lambda s: None)


def test_chunk_respects_size_and_overlap():
    text = "\n\n".join(" ".join(f"p{p}w{i}" for i in range(50)) for p in range(4)) + "\n\n" + " ".join(f"big{i}" for i in range(300))
    chunks = chunk(text, max_words=120, overlap=20)
    assert all(len(c.split()) <= 120 for c in chunks)
    assert chunks[1].split()[:20] == chunks[0].split()[-20:]
    assert " ".join(chunks).count("big299") >= 1
    with pytest.raises(ValueError):
        chunk("x", max_words=10, overlap=10)
