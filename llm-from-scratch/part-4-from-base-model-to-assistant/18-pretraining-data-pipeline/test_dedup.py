"""Tests for dedup.py. Run with:  pytest -q"""
from dedup import MinHasher, estimated_jaccard, fingerprint, jaccard, lsh_candidates, shingles

A = "the quick brown fox jumps over the lazy dog while the cat sleeps in the warm afternoon sun"
B = "the quick brown fox jumps over the lazy dog while the cat naps in the warm afternoon sun"
C = "a completely different sentence about trains, rivers and mountains far away from here today"


def test_fingerprint_ignores_case_and_spacing():
    assert fingerprint("Hello   World\n") == fingerprint("hello world")
    assert fingerprint("Hello World") != fingerprint("Hello World!")


def test_minhash_estimates_jaccard():
    mh = MinHasher(num_perm=256)
    for x, y in [(A, B), (A, C), (A, A)]:
        true = jaccard(shingles(x), shingles(y))
        est = estimated_jaccard(mh.signature(shingles(x)), mh.signature(shingles(y)))
        assert abs(true - est) < 0.15


def test_lsh_finds_the_near_duplicate_only():
    mh = MinHasher(num_perm=128)
    sigs = [mh.signature(shingles(t)) for t in (A, C, B)]
    assert lsh_candidates(sigs, bands=32) == {(0, 2)}
