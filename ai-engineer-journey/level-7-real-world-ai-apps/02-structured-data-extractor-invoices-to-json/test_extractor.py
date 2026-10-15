from pathlib import Path

from extractor import Invoice, LineItem, check_math, extract
from fake_llm import FakeClient


def make(items, subtotal, tax, total):
    return Invoice(vendor="X", invoice_number=None, date=None, currency="USD",
                   line_items=[LineItem(description=d, quantity=q, unit_price=p, total=t) for d, q, p, t in items],
                   subtotal=subtotal, tax=tax, total=total, notes=None)


def test_math_checks_pass_for_correct_invoice():
    inv = make([("logo", 1, 850, 850), ("banners", 6, 45, 270), ("rush", 1, 120, 120)], 1240, 99.2, 1339.2)
    assert check_math(inv) == []


def test_math_checks_catch_a_misread_number():
    inv = make([("banners", 6, 45, 207)], 207, 0, 207)          # 6 x 45 is 270, not 207
    assert any("banners" in p for p in check_math(inv))


def test_extract_uses_structured_output():
    good = make([("tap", 1, 65, 65)], 65, 0, 65)
    fake = FakeClient(parsed=[good])
    inv, problems = extract(fake, Path("samples/messy_note.txt"))
    assert inv.total == 65 and problems == []
    assert fake.calls[0]["output_format"] is Invoice              # the schema was sent to the model
    assert "plumbing" in fake.calls[0]["messages"][0]["content"][0]["text"]


def test_api_returns_json_and_flags_bad_math():
    from fastapi.testclient import TestClient

    import api
    api.client = FakeClient(parsed=[make([("banners", 6, 45, 207)], 207, 0, 207)])
    r = TestClient(api.app).post("/extract", files={"file": ("note.txt", b"6 banners at $45 each, total $207", "text/plain")})
    assert r.status_code == 200
    assert r.json()["needs_review"] is True and "banners" in r.json()["problems"][0]
