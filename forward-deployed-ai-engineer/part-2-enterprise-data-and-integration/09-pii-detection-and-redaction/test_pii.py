import importlib.util
import io

import pytest
from cryptography.fernet import Fernet

import demo
import llm
import pii
from fake_llm import FakeClaude
from safe_logging import get_logger

HAS_NER = importlib.util.find_spec("spacy") is not None and importlib.util.find_spec("en_core_web_sm") is not None


def kinds(text, **kwargs):
    return [(f.kind, f.text) for f in pii.find_pii(text, **kwargs)]


@pytest.mark.parametrize("text, expected", [
    ("mail joost.vandijk@brouwer-metals.example now", ("EMAIL", "joost.vandijk@brouwer-metals.example")),
    ("call +31 6 1234 5678 today", ("PHONE", "+31 6 1234 5678")),
    ("call 06-12345678 today", ("PHONE", "06-12345678")),
    ("IBAN NL91 ABNA 0417 1643 00 please", ("IBAN", "NL91 ABNA 0417 1643 00")),
    ("IBAN DE89370400440532013000.", ("IBAN", "DE89370400440532013000")),
    ("card 4111-1111-1111-1111 ok", ("CREDIT_CARD", "4111-1111-1111-1111")),
    ("from 192.168.10.24 at night", ("IP_ADDRESS", "192.168.10.24")),
    ("Kind regards,\nAnna Kowalska\n", ("PERSON", "Anna Kowalska")),
    ("Hi, my name is Sam Lee and", ("PERSON", "Sam Lee")),
])
def test_each_kind_is_found(text, expected):
    assert expected in kinds(text)


def test_business_data_is_not_mistaken_for_pii():
    text = "Tracking NW-4821907, invoice INV-2291, 1,250.00 EUR, promised 2026-10-20, ticket T-1042, 10% credit."
    assert kinds(text) == []


def test_checksums_reject_lookalikes():
    assert ("CREDIT_CARD", "4111 1111 1111 1112") not in kinds("card 4111 1111 1111 1112")   # fails Luhn
    assert all(k != "IBAN" for k, _ in kinds("NL91 ABNA 0417 1643 01"))                    # fails mod-97
    assert pii.luhn_ok("4111111111111111") and pii.iban_ok("GB82 WEST 1234 5698 7654 32")


def test_known_names_and_overlaps():
    found = kinds("Joost van Dijk wrote to Joost.", known_names=["Joost van Dijk", "Joost"])
    assert found == [("PERSON", "Joost van Dijk"), ("PERSON", "Joost")]   # the longer name wins where they overlap


def test_mask_is_one_way():
    assert pii.mask("Call +31 6 1234 5678 or joost@x.example") == "Call [PHONE] or [EMAIL]"


def test_pseudonymise_is_consistent_and_reversible():
    shield = pii.Pseudonymiser(known_names=["Joost van Dijk"])
    first = shield.pseudonymise("Joost van Dijk: NL91 ABNA 0417 1643 00")
    second = shield.pseudonymise("Pay NL91ABNA0417164300 to joost van dijk")          # same values, other spelling
    assert first == "<PERSON_1>: <IBAN_1>" and second == "Pay <IBAN_1> to <PERSON_1>"
    assert shield.restore("Dear <PERSON_1>, paid to <IBAN_1>. <PERSON_7>") == \
        "Dear Joost van Dijk, paid to NL91 ABNA 0417 1643 00. <PERSON_7>"          # invented placeholder left alone


def test_vault_can_be_stored_encrypted():
    key = Fernet.generate_key()
    shield = pii.Pseudonymiser()
    shield.pseudonymise("mail a.b@c.example")
    locked = shield.export_vault(key)
    assert b"a.b@c.example" not in locked
    other = pii.Pseudonymiser()
    other.import_vault(key, locked)
    assert other.restore("<EMAIL_1>") == "a.b@c.example"


def test_logs_are_masked_even_when_developers_log_content():
    stream = io.StringIO()
    log = get_logger("test-logger", stream=stream)
    log.info("customer %s paid with %s", "joost@brouwer.example", "4111 1111 1111 1111")
    assert "joost@" not in stream.getvalue() and "[EMAIL]" in stream.getvalue() and "[CREDIT_CARD]" in stream.getvalue()


def test_llm_never_sees_pii_and_reply_is_restored(monkeypatch, capsys):
    fake = FakeClaude(text="Dear <PERSON_2>, we'll call <PHONE_1>.")
    monkeypatch.setattr(llm, "PROVIDER", "anthropic")
    monkeypatch.setattr(llm, "_client", fake)
    monkeypatch.setattr("sys.argv", ["demo.py"])
    demo.main()
    sent = str(fake.calls)
    for secret in ["Joost van Dijk", "NL91", "4111", "+31 6", "192.168.10.24", "brouwer-metals.example"]:
        assert secret not in sent
    assert "Dear Joost van Dijk, we'll call +31 6 1234 5678." in capsys.readouterr().out


@pytest.mark.skipif(not HAS_NER, reason="optional: pip install -r requirements-optional.txt")
def test_ner_finds_names_nobody_listed():
    assert ("PERSON", "Pieter Bakker") in kinds("but your driver Pieter Bakker never came.", use_ner=True)
    assert ("PERSON", "Pieter Bakker") not in kinds("but your driver Pieter Bakker never came.")
