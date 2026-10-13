"""Project 5.6: Byte-Pair Encoding (BPE), the tokenizer family used by GPT models, from scratch.

Idea: start with single bytes, then repeatedly MERGE the most frequent neighbouring pair into a new token.
Frequent chunks ("the", "ing", " to") become single tokens; rare words stay as several pieces.
"""
from collections import Counter


class BPETokenizer:
    def __init__(self):
        self.merges: dict[tuple[int, int], int] = {}            # (a, b) -> new token id
        self.vocab: dict[int, bytes] = {i: bytes([i]) for i in range(256)}

    @staticmethod
    def _pairs(ids):
        return Counter(zip(ids, ids[1:]))

    @staticmethod
    def _merge(ids, pair, new_id):
        out, i = [], 0
        while i < len(ids):
            if i < len(ids) - 1 and (ids[i], ids[i + 1]) == pair:
                out.append(new_id); i += 2
            else:
                out.append(ids[i]); i += 1
        return out

    def train(self, text: str, vocab_size: int, verbose=False):
        ids = list(text.encode("utf-8"))                         # start from raw bytes (works for ANY language/emoji)
        for new_id in range(256, vocab_size):
            pairs = self._pairs(ids)
            if not pairs:
                break
            pair = max(pairs, key=pairs.get)                     # most frequent neighbouring pair
            ids = self._merge(ids, pair, new_id)
            self.merges[pair] = new_id
            self.vocab[new_id] = self.vocab[pair[0]] + self.vocab[pair[1]]
            if verbose and new_id < 266:
                print(f"merge #{new_id - 255:2d}: {self.vocab[pair[0]]!r} + {self.vocab[pair[1]]!r} -> {self.vocab[new_id]!r}  (seen {pairs[pair]}x)")
        return self

    def encode(self, text: str) -> list[int]:
        ids = list(text.encode("utf-8"))
        while len(ids) >= 2:
            # apply merges in the order they were learned (lowest new id first)
            pair = min(self._pairs(ids), key=lambda p: self.merges.get(p, float("inf")))
            if pair not in self.merges:
                break
            ids = self._merge(ids, pair, self.merges[pair])
        return ids

    def decode(self, ids: list[int]) -> str:
        return b"".join(self.vocab[i] for i in ids).decode("utf-8", errors="replace")


if __name__ == "__main__":
    text = open(__file__.replace("bpe.py", "training_text.txt"), encoding="utf-8").read()
    tok = BPETokenizer().train(text, vocab_size=400, verbose=True)

    sample = "The tokenizer learns that common words are worth a single token. 🤖"
    ids = tok.encode(sample)
    print(f"\n'{sample}'\n-> {len(sample.encode())} bytes became {len(ids)} tokens")
    print("pieces:", [tok.vocab[i].decode('utf-8', 'replace') for i in ids])
    print("(the 4 '�' pieces are the emoji's 4 bytes: one byte alone isn't valid text, but together they decode fine)")
    assert tok.decode(ids) == sample, "round trip failed!"
    print("✅ decode(encode(text)) == text")

    try:
        import tiktoken
        gpt = tiktoken.get_encoding("cl100k_base")
        print(f"\nFor comparison, a real GPT tokenizer (100k vocab) uses {len(gpt.encode(sample))} tokens:",
              [gpt.decode([t]) for t in gpt.encode(sample)])
    except Exception:
        print("\n(pip install tiktoken to compare with a real GPT tokenizer)")
