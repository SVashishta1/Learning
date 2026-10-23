"""PII redaction: what a model may see, and what stays on this machine."""
from privacy import Vault, find_leaks, redact


def test_redacts_common_personal_details_and_restores_them_locally():
    v = Vault()
    text = ("This is Aisha Khan, call me on 07700 900 123 or aisha.k@example.com. I live at 4 Mill Lane. "
            "Born 12/03/1990, ID 123-45-6789. My daughter Zara is 2.")
    out = redact(text, v)
    assert out == ("This is [NAME_1], call me on [PHONE_1] or [EMAIL_1]. I live at [ADDRESS_1]. "
                   "Born [DATE_1], ID [IDNUM_1]. My daughter [NAME_2] is 2.")
    assert find_leaks(out, v) == []
    assert v.restore(out) == text


def test_spanish_clues_and_money_are_handled():
    v = Vault()
    out = redact("Me llamo María López. Ganamos 3.600 al mes y pagamos 1.100 de renta.", v)
    assert out == "Me llamo [NAME_1]. Ganamos 3.600 al mes y pagamos 1.100 de renta."     # money is not a phone


def test_known_names_box_catches_names_without_a_clue_word():
    v = Vault()
    out = redact("Leo and Mia go to school. Leo is 8.", v, known_names=["Leo", "Mia"])
    assert out == "[NAME_1] and [NAME_2] go to school. [NAME_1] is 8."


def test_lowercase_words_after_clues_are_not_names():
    assert redact("I'm a single mum and I am working.", Vault()) == "I'm a single mum and I am working."
