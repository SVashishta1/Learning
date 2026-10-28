"""Tests for bpe.py. Run with:  pytest -q"""
from bpe import BasicTokenizer, RegexTokenizer, get_stats, merge

TEXT = ("The quick brown fox jumps over the lazy dog. The dog sleeps; the fox runs!\n"
        "Numbers 1234567 and émojis 🤖 and Hindi नमस्ते must survive a round trip.") * 3


def test_helpers():
    assert get_stats([1, 2, 3, 1, 2]) == {(1, 2): 2, (2, 3): 1, (3, 1): 1}
    assert merge([5, 6, 6, 7, 5, 6], (5, 6), 256) == [256, 6, 7, 256]


def test_wikipedia_example():
    tok = BasicTokenizer()
    tok.train("aaabdaaabac", 256 + 3)
    assert tok.encode("aaabdaaabac") == [258, 100, 258, 97, 99]
    assert tok.decode([258, 100, 258, 97, 99]) == "aaabdaaabac"


def test_round_trip_both_tokenizers():
    for tok in (BasicTokenizer(), RegexTokenizer()):
        tok.train(TEXT, 256 + 50)
        ids = tok.encode(TEXT)
        assert len(ids) < len(TEXT.encode("utf-8"))        # it compresses
        assert tok.decode(ids) == TEXT                     # and loses nothing


def test_special_tokens_and_save_load(tmp_path):
    tok = RegexTokenizer()
    tok.train(TEXT, 256 + 30)
    tok.register_special_tokens({"<|endoftext|>": 286})
    ids = tok.encode("dog<|endoftext|>fox", allowed_special="all")
    assert 286 in ids and tok.decode(ids) == "dog<|endoftext|>fox"
    assert 286 not in tok.encode("dog<|endoftext|>fox", allowed_special="none")
    tok.save(str(tmp_path / "t"))
    again = RegexTokenizer().load(str(tmp_path / "t.model"))
    assert again.encode(TEXT) == tok.encode(TEXT)
    assert again.encode("a<|endoftext|>b", allowed_special="all") == tok.encode("a<|endoftext|>b", allowed_special="all")
