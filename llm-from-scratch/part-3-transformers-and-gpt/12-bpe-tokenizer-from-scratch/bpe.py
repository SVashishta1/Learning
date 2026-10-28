"""A byte-level BPE (Byte-Pair Encoding) tokenizer, built from scratch.

Same ideas and names as Karpathy's minbpe (github.com/karpathy/minbpe):
    BasicTokenizer  - BPE on the raw bytes of the whole text
    RegexTokenizer  - first splits text into chunks with a regex (like GPT-2 / GPT-4),
                      then runs BPE inside each chunk; also supports special tokens
Read top to bottom: helpers -> Tokenizer (shared parts) -> BasicTokenizer -> RegexTokenizer.
"""
from collections import Counter

import regex as re   # the 'regex' package: like Python's 're', but understands \p{L} (= any letter)

# The exact split patterns used by OpenAI's GPT-2 and GPT-4 (cl100k_base) tokenizers.
GPT2_SPLIT_PATTERN = r"""'(?:[sdmt]|ll|ve|re)| ?\p{L}+| ?\p{N}+| ?[^\s\p{L}\p{N}]+|\s+(?!\S)|\s+"""
GPT4_SPLIT_PATTERN = r"""'(?i:[sdmt]|ll|ve|re)|[^\r\n\p{L}\p{N}]?+\p{L}+|\p{N}{1,3}| ?[^\s\p{L}\p{N}]++[\r\n]*|\s*[\r\n]|\s+(?!\S)|\s+"""


# ----------------------------------------------------------------------------- helpers
def get_stats(ids, counts=None, weight=1):
    """Count neighbouring pairs. [1, 2, 3, 1, 2] -> {(1, 2): 2, (2, 3): 1, (3, 1): 1}.
    `weight` lets us count a chunk that appears 500 times in one go (500 instead of 1)."""
    counts = {} if counts is None else counts
    for pair in zip(ids, ids[1:]):          # (ids[0], ids[1]), (ids[1], ids[2]), ...
        counts[pair] = counts.get(pair, 0) + weight
    return counts


def merge(ids, pair, idx):
    """Replace every occurrence of `pair` in `ids` by the new token `idx`.
    merge([5, 6, 6, 7, 5, 6], pair=(5, 6), idx=256) -> [256, 6, 7, 256]"""
    out, i = [], 0
    while i < len(ids):
        if i < len(ids) - 1 and ids[i] == pair[0] and ids[i + 1] == pair[1]:
            out.append(idx)
            i += 2                          # skip both members of the pair
        else:
            out.append(ids[i])
            i += 1
    return out


def render_token(b: bytes) -> str:
    """Bytes -> printable text for the .vocab file (broken UTF-8 pieces become '�', control chars are escaped)."""
    s = b.decode("utf-8", errors="replace")
    return "".join(ch if ch.isprintable() else f"\\u{ord(ch):04x}" for ch in s)


# ----------------------------------------------------------------------------- shared base class
class Tokenizer:
    def __init__(self):
        self.merges = {}            # (id, id) -> new id, in the order they were learned
        self.special_tokens = {}    # e.g. {'<|endoftext|>': 512}
        self.pattern = ""
        self.vocab = self._build_vocab()

    def _build_vocab(self):
        """id -> bytes. 0..255 are the raw bytes; every merge adds one longer byte string."""
        vocab = {i: bytes([i]) for i in range(256)}
        for (a, b), idx in self.merges.items():           # dicts keep insertion order = merge order
            vocab[idx] = vocab[a] + vocab[b]
        for s, idx in self.special_tokens.items():
            vocab[idx] = s.encode("utf-8")
        return vocab

    def decode(self, ids):
        """Ids -> text. Look up each id's bytes, glue them, decode the UTF-8."""
        data = b"".join(self.vocab[i] for i in ids)
        return data.decode("utf-8", errors="replace")     # 'replace': never crash on half a character

    def _encode_chunk(self, ids):
        """Apply the learned merges to one list of byte ids, earliest-learned merge first."""
        while len(ids) >= 2:
            stats = get_stats(ids)
            pair = min(stats, key=lambda p: self.merges.get(p, float("inf")))  # the oldest merge we know
            if pair not in self.merges:
                break                                       # nothing left to merge
            ids = merge(ids, pair, self.merges[pair])
        return ids

    def save(self, prefix):
        """Write prefix.model (what load() needs) and prefix.vocab (for humans to read)."""
        with open(prefix + ".model", "w", encoding="utf-8") as f:
            f.write("minbpe v1\n")
            f.write(self.pattern + "\n")
            f.write(f"{len(self.special_tokens)}\n")
            for s, idx in self.special_tokens.items():
                f.write(f"{s} {idx}\n")
            for a, b in self.merges:
                f.write(f"{a} {b}\n")
        inverted = {idx: pair for pair, idx in self.merges.items()}
        with open(prefix + ".vocab", "w", encoding="utf-8") as f:
            for idx, token in self.vocab.items():
                if idx in inverted:
                    a, b = inverted[idx]
                    f.write(f"[{render_token(self.vocab[a])}][{render_token(self.vocab[b])}] -> [{render_token(token)}] {idx}\n")
                else:
                    f.write(f"[{render_token(token)}] {idx}\n")

    def load(self, model_file):
        with open(model_file, encoding="utf-8") as f:
            assert f.readline().strip() == "minbpe v1", "not a tokenizer file written by save()"
            self.pattern = f.readline().rstrip("\n")
            n_special = int(f.readline())
            special = {}
            for _ in range(n_special):
                s, idx = f.readline().split()
                special[s] = int(idx)
            merges, idx = {}, 256
            for line in f:
                a, b = map(int, line.split())
                merges[(a, b)] = idx
                idx += 1
        self.merges = merges
        self._cache = {}                                    # forget chunks encoded with old merges
        if hasattr(self, "register_special_tokens"):
            self.compiled_pattern = re.compile(self.pattern)
            self.register_special_tokens(special)
        self.vocab = self._build_vocab()
        return self


# ----------------------------------------------------------------------------- 1) the basic version
class BasicTokenizer(Tokenizer):
    """BPE straight on the bytes of the whole text. Simple, but merges happily cross
    word boundaries and punctuation ('d, ' or 'e t' become tokens)."""

    def train(self, text, vocab_size, verbose=False):
        assert vocab_size >= 256
        ids = list(text.encode("utf-8"))                  # text -> bytes -> list of numbers 0..255
        self.merges = {}
        for i in range(vocab_size - 256):
            stats = get_stats(ids)
            if not stats:
                break
            pair = max(stats, key=stats.get)               # the most frequent neighbouring pair
            idx = 256 + i                                  # its new token id
            ids = merge(ids, pair, idx)
            self.merges[pair] = idx
            if verbose:
                self.vocab = self._build_vocab()
                print(f"merge {i + 1:3d}: {self.vocab[pair[0]]} + {self.vocab[pair[1]]} -> {self.vocab[idx]} (seen {stats[pair]}x)")
        self.vocab = self._build_vocab()

    def encode(self, text):
        return self._encode_chunk(list(text.encode("utf-8")))


# ----------------------------------------------------------------------------- 2) the GPT-4 style version
class RegexTokenizer(Tokenizer):
    """Split text into chunks first (words, numbers, punctuation, spaces), then BPE inside each chunk.
    Merges can never cross a chunk border, so 'dog.' and 'dog!' share the token 'dog'."""

    def __init__(self, pattern=GPT4_SPLIT_PATTERN):
        super().__init__()
        self.pattern = pattern
        self.compiled_pattern = re.compile(pattern)
        self.inverse_special_tokens = {}

    def train(self, text, vocab_size, verbose=False):
        assert vocab_size >= 256
        # Speed trick: the same chunk (' the', ' and', ...) appears thousands of times.
        # Count each DISTINCT chunk once and remember how often it occurs.
        chunk_counts = Counter(re.findall(self.compiled_pattern, text))
        words = [list(chunk.encode("utf-8")) for chunk in chunk_counts]
        freqs = list(chunk_counts.values())
        self.merges = {}
        for i in range(vocab_size - 256):
            stats = {}
            for w, f in zip(words, freqs):
                get_stats(w, stats, weight=f)              # pairs inside each chunk, times how often it occurs
            if not stats:
                break
            pair = max(stats, key=stats.get)
            idx = 256 + i
            words = [merge(w, pair, idx) if len(w) > 1 else w for w in words]
            self.merges[pair] = idx
            if verbose:
                self.vocab = self._build_vocab()
                print(f"merge {i + 1:3d}: {self.vocab[pair[0]]} + {self.vocab[pair[1]]} -> {self.vocab[idx]} (seen {stats[pair]}x)")
        self.vocab = self._build_vocab()
        self._cache = {}

    def register_special_tokens(self, special_tokens):
        """special_tokens: {'<|endoftext|>': 512, ...}. They are never produced by merges;
        they are 'reserved words' you insert on purpose (end of a document, start of a chat turn...)."""
        self.special_tokens = dict(special_tokens)
        self.inverse_special_tokens = {v: k for k, v in special_tokens.items()}
        self.vocab = self._build_vocab()

    def encode_ordinary(self, text):
        """Encode text, treating '<|endoftext|>' etc. as plain characters."""
        if not hasattr(self, "_cache"):
            self._cache = {}
        ids = []
        for chunk in re.findall(self.compiled_pattern, text):
            if chunk not in self._cache:                   # memory: each distinct chunk is encoded once
                self._cache[chunk] = self._encode_chunk(list(chunk.encode("utf-8")))
            ids.extend(self._cache[chunk])
        return ids

    def encode(self, text, allowed_special="none_raise"):
        """allowed_special: 'all' = turn special-token strings into their ids,
        'none' = treat them as normal text, 'none_raise' = complain if one appears (the safe default,
        same as tiktoken: users should not be able to type your control tokens by accident)."""
        if allowed_special == "all":
            special = self.special_tokens
        elif allowed_special == "none":
            special = {}
        elif allowed_special == "none_raise":
            special = {}
            assert all(s not in text for s in self.special_tokens), "text contains a special token; pass allowed_special='all'"
        elif isinstance(allowed_special, set):
            special = {k: v for k, v in self.special_tokens.items() if k in allowed_special}
        else:
            raise ValueError(f"allowed_special={allowed_special} not understood")
        if not special:
            return self.encode_ordinary(text)
        # Split around the special strings, e.g. 'Hi<|endoftext|>Yo' -> ['Hi', '<|endoftext|>', 'Yo']
        special_pattern = "(" + "|".join(re.escape(s) for s in special) + ")"
        ids = []
        for part in re.split(special_pattern, text):
            if part in special:
                ids.append(special[part])
            elif part:
                ids.extend(self.encode_ordinary(part))
        return ids

    def decode(self, ids):
        parts = []
        for i in ids:
            parts.append(self.inverse_special_tokens[i].encode("utf-8") if i in self.inverse_special_tokens else self.vocab[i])
        return b"".join(parts).decode("utf-8", errors="replace")
