import json

import pytest

import ingest
import make_samples


@pytest.fixture(scope="module")
def samples(tmp_path_factory):
    folder = tmp_path_factory.mktemp("samples")
    make_samples.main(folder)
    return folder


def texts(chunks):
    return "\n".join(c["text"] for c in chunks)


def test_pdf_headers_footers_and_hyphens_are_fixed(samples):
    chunks, warnings = ingest.ingest_file(samples / "delivery_terms.pdf")
    body = texts(chunks)
    assert "General Delivery Terms v4.2" not in body and "Confidential" not in body
    assert "delivery time" in body and "deliv-" not in body and "request within 2 working days" in body
    assert [c["metadata"]["page"] for c in chunks] == [1, 2]
    assert warnings == ["page 3 has no text layer (scanned image?): needs OCR"]


def test_excel_merged_cells_header_and_notes(samples):
    chunks, _ = ingest.ingest_file(samples / "rate_card_brouwer.xlsx")
    rates = chunks[0]
    assert rates["metadata"]["sheet"] == "Rates" and rates["metadata"]["rows"] == "4-9"
    assert rates["text"].count("Zone: NL;") == 3                  # merged cell copied down to all its rows
    assert "Prices exclude VAT" in rates["text"] and "nan" not in rates["text"]
    assert "Surcharge: Fuel; Amount: 7.5; Unit: % of price" in texts(chunks)


def test_email_drops_reply_chain_and_signature(samples):
    chunks, _ = ingest.ingest_file(samples / "customer_email.eml")
    body = chunks[0]["text"]
    assert "production line in Utrecht" in body
    assert "will arrive tomorrow" not in body and "+31 30" not in body and "confidential" not in body
    assert chunks[0]["metadata"]["attachments"] == ["missing_parts.csv"]
    assert chunks[1]["metadata"]["attachment"] == "missing_parts.csv" and "Steel bracket" in chunks[1]["text"]


def test_html_keeps_content_drops_junk(samples):
    chunks, _ = ingest.ingest_file(samples / "faq.html")
    body = texts(chunks)
    assert "cookies" not in body and "Home" not in body and "volume discounts" not in body and "track(" not in body
    assert [c["metadata"]["section"] for c in chunks][0] == "How do I track my shipment?"
    assert "final packing list" in body                           # the 'ﬁ' ligature became plain 'fi'


def test_normalise():
    assert ingest.normalise("a  b\t\tc\n\n\n\nd ﬁne") == "a b c\n\nd fine"


def test_chunks_respect_size_and_overlap():
    paragraphs = [f"Paragraph {i}: " + "word " * 30 for i in range(10)]
    chunks = ingest.chunk_text("\n".join(paragraphs), max_chars=400, overlap_chars=200)
    assert all(len(c) <= 400 for c in chunks)
    assert len(chunks) > 1
    assert chunks[1].split("\n")[0] == chunks[0].split("\n")[-1]   # the last paragraph is repeated as context
    assert ingest.chunk_text("x" * 2000, max_chars=500) == ["x" * 500]  # a giant 'sentence' is cut, not lost


def test_folder_skips_unknown_reports_broken_and_dedupes(samples, tmp_path):
    for path in samples.iterdir():
        (tmp_path / path.name).write_bytes(path.read_bytes())
    (tmp_path / "copy_of_faq.html").write_bytes((samples / "faq.html").read_bytes())
    (tmp_path / "notes.docx").write_text("not supported")
    (tmp_path / "broken.pdf").write_text("this is not a pdf")
    chunks, report = ingest.ingest_folder(tmp_path)
    notes = {name: (count, warnings) for name, count, warnings in report}
    assert notes["notes.docx"][1] == ["skipped: unsupported file type"]
    assert notes["broken.pdf"][1][0].startswith("FAILED")
    assert notes["copy_of_faq.html"][0] == 3 and notes["faq.html"][0] == 0   # same text: kept once (A-Z order)
    ids = [c["id"] for c in chunks]
    assert len(ids) == len(set(ids)) == 9
    json.dumps(chunks)                                             # every chunk can be saved as JSON
