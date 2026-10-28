"""Finding duplicates: exact (a fingerprint per document) and near (MinHash + LSH), from scratch.

Used by pipeline.py. Run this file on its own for a small demo:  python dedup.py
"""
import hashlib
import re
import zlib
from collections import defaultdict

import numpy as np


# ----------------------------------------------------------------------------- exact duplicates
def normalize(text):
    """Lower-case and squash all whitespace, so 'Hello   World' and 'hello world' count as the same."""
    return " ".join(text.lower().split())


def fingerprint(text):
    """SHA-256 of the normalised text: 64 hex characters that are (practically) unique per text."""
    return hashlib.sha256(normalize(text).encode("utf-8")).hexdigest()


# ----------------------------------------------------------------------------- near duplicates
def shingles(text, n=5):
    """All runs of n consecutive words ('shingles'), as a set. Small edits change only a few of them."""
    words = re.findall(r"\w+", text.lower())
    if len(words) < n:
        return {" ".join(words)}
    return {" ".join(words[i:i + n]) for i in range(len(words) - n + 1)}


def jaccard(a, b):
    """|A ∩ B| / |A ∪ B|: shared shingles divided by all distinct shingles. 1 = identical sets, 0 = nothing shared."""
    return len(a & b) / max(1, len(a | b))


class MinHasher:
    """A MinHash signature: num_perm small numbers per document such that the fraction of positions
    where two signatures agree is (on average) equal to the Jaccard similarity of their shingle sets."""

    def __init__(self, num_perm=128, seed=0):
        rng = np.random.default_rng(seed)
        # num_perm different random hash functions h(x) = (a*x + b) >> 32  ("multiply-shift" hashing)
        self.a = rng.integers(1, 2**63, size=num_perm, dtype=np.uint64) | np.uint64(1)   # odd numbers
        self.b = rng.integers(0, 2**63, size=num_perm, dtype=np.uint64)

    def signature(self, shingle_set):
        x = np.array([zlib.crc32(s.encode("utf-8")) for s in shingle_set], dtype=np.uint64)   # each shingle -> a number
        with np.errstate(over="ignore"):                                                       # wrap-around is intended
            h = (self.a[:, None] * x[None, :] + self.b[:, None]) >> np.uint64(32)              # (num_perm, n_shingles)
        return h.min(axis=1)                                                                   # the MIN of each hash function


def estimated_jaccard(sig1, sig2):
    return float((sig1 == sig2).mean())


def lsh_candidates(signatures, bands=32):
    """Locality-Sensitive Hashing: cut each signature into `bands` pieces; two documents become candidates
    if ANY piece is exactly equal. Similar documents almost surely share a piece; different ones almost never do.
    This avoids comparing every document with every other (n² pairs)."""
    rows = len(signatures[0]) // bands
    pairs = set()
    for band in range(bands):
        buckets = defaultdict(list)
        for doc_id, sig in enumerate(signatures):
            buckets[sig[band * rows:(band + 1) * rows].tobytes()].append(doc_id)
        for ids in buckets.values():
            for i in range(len(ids)):
                for j in range(i + 1, len(ids)):
                    pairs.add((ids[i], ids[j]))
    return pairs


if __name__ == "__main__":
    a = "Alice was beginning to get very tired of sitting by her sister on the bank, and of having nothing to do."
    texts = {
        "punctuation changed": "Alice was beginning to get very tired of sitting by her sister on the bank and of having nothing to do!",
        "one word added": "Alice was beginning to get very tired of sitting by her sister on the river bank, and of having nothing to do.",
        "reworded": "Alice was starting to get really tired of sitting next to her sister on the bank, with nothing at all to do.",
        "another book": "It is a truth universally acknowledged, that a single man in possession of a good fortune, must be in want of a wife.",
    }
    mh = MinHasher()
    sa = shingles(a)
    print("exact fingerprint equal for 'punctuation changed'?", fingerprint(a) == fingerprint(texts["punctuation changed"]))
    for name, t in texts.items():
        st = shingles(t)
        print(f"{name:20s} true Jaccard {jaccard(sa, st):.2f} | MinHash estimate {estimated_jaccard(mh.signature(sa), mh.signature(st)):.2f}")
