"""Lesson 12: train BPE tokenizers from scratch and look inside them.

python train_tokenizer.py              # vocab 512 (256 bytes + 256 merges), ~1 min on a laptop
python train_tokenizer.py --vocab 1024 # more merges = longer tokens = fewer tokens per text
"""
import argparse
import os
import time
import urllib.request

from bpe import BasicTokenizer, RegexTokenizer

URL = "https://raw.githubusercontent.com/karpathy/char-rnn/master/data/tinyshakespeare/input.txt"
parser = argparse.ArgumentParser()
parser.add_argument("--vocab", type=int, default=512, help="final vocabulary size (must be > 256)")
args = parser.parse_args()


def show(tok, text):
    """Print how `text` is cut into tokens: [piece][piece][piece]"""
    ids = tok.encode(text) if not isinstance(tok, RegexTokenizer) else tok.encode(text, allowed_special="all")
    pieces = [tok.decode([i]) for i in ids]
    print(f"  {len(text.encode('utf-8'))} bytes -> {len(ids)} tokens: " + "".join("[" + p.replace("\n", "\\n") + "]" for p in pieces))
    return ids


print("=" * 70 + "\n1) The classic tiny example (Wikipedia): 'aaabdaaabac'\n")
tiny = BasicTokenizer()
tiny.train("aaabdaaabac", vocab_size=256 + 3, verbose=True)
print("  encoded:", tiny.encode("aaabdaaabac"), "  (97='a', 98='b', 99='c', 100='d')")

if not os.path.exists("input.txt"):
    print("\ndownloading tinyshakespeare (1 MB)...")
    urllib.request.urlretrieve(URL, "input.txt")
text = open("input.txt", encoding="utf-8").read()
n = int(0.9 * len(text))
train_text, val_text = text[:n], text[n:]          # train on 90%, test compression on the unseen 10%
print(f"\nShakespeare: {len(text):,} characters ({len(train_text):,} for training, {len(val_text):,} held out)")

print("=" * 70 + "\n2) BasicTokenizer: BPE on raw bytes (first 100,000 characters, 40 merges)\n")
basic = BasicTokenizer()
basic.train(train_text[:100_000], vocab_size=256 + 40)
learned = [basic.vocab[i] for i in range(256, 296)]
print("  some learned tokens:", learned[-12:])
print("  notice tokens that glue a word to its neighbour's space or punctuation: that's the problem regex fixes")

print("=" * 70 + f"\n3) RegexTokenizer (GPT-4 split pattern), vocab {args.vocab}\n")
sample = "To be, or not to be: that is the question."
print("  regex chunks of the sample:", RegexTokenizer().compiled_pattern.findall(sample))
tok = RegexTokenizer()
t0 = time.time()
tok.train(train_text, vocab_size=args.vocab)
print(f"  trained {len(tok.merges)} merges in {time.time() - t0:.1f}s")
print("  first 10 merges:", [tok.vocab[256 + i] for i in range(10)])
print("  last 10 merges: ", [tok.vocab[args.vocab - 10 + i] for i in range(10)])

print("\n  How texts are cut:")
for s in [sample, "ROMEO:\nWhat light through yonder window breaks?", "Tokenization of 2024 emails 🤖"]:
    ids = show(tok, s)
    assert tok.decode(ids) == s                     # the golden rule: decode(encode(x)) == x
print("  decode(encode(x)) == x for every sample  ✓")

val_ids = tok.encode(val_text)
print(f"\n  held-out text: {len(val_text.encode('utf-8')):,} bytes -> {len(val_ids):,} tokens "
      f"= {len(val_text.encode('utf-8')) / len(val_ids):.2f} bytes per token (compression ratio)")

print("=" * 70 + "\n4) Special tokens\n")
eot = args.vocab                                       # the first id after all normal tokens
tok.register_special_tokens({"<|endoftext|>": eot})
ids = show(tok, "The end.<|endoftext|>A new story")
print(f"  '<|endoftext|>' became the single id {eot}: {eot in ids}")
try:
    tok.encode("a user typed <|endoftext|> here")       # default: refuse, like tiktoken
except AssertionError as e:
    print("  safe default when the special string appears in normal text:", e)

tok.save("shakespeare")
again = RegexTokenizer().load("shakespeare.model")
assert again.encode(val_text[:5000]) == tok.encode(val_text[:5000])
print("\nsaved shakespeare.model + shakespeare.vocab and reloaded them: same encoding  ✓")
