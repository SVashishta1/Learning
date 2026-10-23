"""Lesson 12: compare your tokenizer with the real GPT-2 and GPT-4 tokenizers (tiktoken).

python compare_tiktoken.py
Needs: `pip install tiktoken`, and internet the first time (tiktoken downloads each vocabulary once).
Run train_tokenizer.py first if you also want your own tokenizer in the table.
"""
import os

import regex as re

from bpe import GPT2_SPLIT_PATTERN, GPT4_SPLIT_PATTERN, RegexTokenizer

SAMPLES = [
    "To be, or not to be: that is the question.",
    "Hello world! HELLO WORLD!",
    "    for i in range(10):\n        print(i)",   # code: GPT-2 wastes one token per space, GPT-4 groups them
    "Order #123456789 costs $49.99",               # numbers: GPT-4 cuts them into groups of up to 3 digits
    "नमस्ते दुनिया",                                  # Hindi ("hello world"): many more tokens than English
    "I'm sure you've seen it 🤖",
]

print("1) The regex pre-split (no download needed)\n")
for s in SAMPLES[2:4]:
    print("  text:", repr(s))
    print("  GPT-2 chunks:", re.findall(GPT2_SPLIT_PATTERN, s))
    print("  GPT-4 chunks:", re.findall(GPT4_SPLIT_PATTERN, s), "\n")

tokenizers = {}
if os.path.exists("shakespeare.model"):
    ours = RegexTokenizer().load("shakespeare.model")
    tokenizers[f"ours ({len(ours.vocab)})"] = lambda s: [ours.decode([i]) for i in ours.encode(s, allowed_special="all")]
try:
    import tiktoken
    for name in ["gpt2", "cl100k_base"]:      # GPT-2 (50,257 tokens) and GPT-4 (100,277 tokens)
        enc = tiktoken.get_encoding(name)
        # decode_single_token_bytes shows the exact bytes; broken UTF-8 pieces print as '�'
        tokenizers[f"{name} ({enc.n_vocab:,})"] = (
            lambda s, enc=enc: [enc.decode_single_token_bytes(t).decode("utf-8", errors="replace") for t in enc.encode(s)])
except Exception as e:                        # not installed, or no internet for the first download
    print(f"(tiktoken not available: {type(e).__name__}. `pip install tiktoken` and run again with internet.)\n")

print("2) Token counts (fewer tokens = cheaper and fits more text in the context window)\n")
names = list(tokenizers)
print(f"  {'text':44s}" + "".join(f"{n:>22s}" for n in names))
for s in SAMPLES:
    print(f"  {repr(s)[:44]:44s}" + "".join(f"{len(tokenizers[n](s)):>22d}" for n in names))

print("\n3) How each tokenizer cuts the code sample\n")
for n in names:
    print(f"  {n:22s}", "".join("[" + p.replace("\n", "\\n") + "]" for p in tokenizers[n](SAMPLES[2])))
