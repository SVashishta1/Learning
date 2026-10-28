"""Capstone stage 2: train YOUR BPE tokenizer (lesson 12) on the corpus, then tokenize the corpus.

python tokenizer.py                # vocab 1,024 + 4 special tokens, ~1-2 min
python tokenizer.py --vocab 2048   # longer tokens, slower training
-> data/tok.model, data/train.npy, data/val.npy
"""
import argparse
import json
import time

import numpy as np

from bpe import GPT4_SPLIT_PATTERN, RegexTokenizer
from common import SPECIALS, TOKENIZER_FILE

p = argparse.ArgumentParser()
p.add_argument("--vocab", type=int, default=1024)
args = p.parse_args()

docs = [json.loads(line) for line in open("data/documents.jsonl", encoding="utf-8")]
train_text = "\n\n".join(d["text"] for d in docs if d["split"] == "train")

tok = RegexTokenizer(GPT4_SPLIT_PATTERN)
t0 = time.time()
tok.train(train_text, vocab_size=args.vocab)
tok.register_special_tokens({s: args.vocab + i for i, s in enumerate(SPECIALS)})   # 1024..1027
tok.save(TOKENIZER_FILE[:-len(".model")])
print(f"trained {len(tok.merges)} merges in {time.time() - t0:.0f}s -> {TOKENIZER_FILE}")
print("last 12 tokens learned:", [tok.vocab[i].decode('utf-8', 'replace') for i in range(args.vocab - 12, args.vocab)])

eot = tok.special_tokens["<|endoftext|>"]
for split in ("train", "val"):
    ids = []
    for d in docs:
        if d["split"] == split:
            ids.append(eot)                                  # a document starts here
            ids.extend(tok.encode_ordinary(d["text"]))
    arr = np.array(ids, dtype=np.uint16)                     # all ids < 65,536 -> 2 bytes each
    np.save(f"data/{split}.npy", arr)
    chars = sum(len(d["text"]) for d in docs if d["split"] == split)
    print(f"{split}: {chars:,} characters -> {len(arr):,} tokens ({chars / len(arr):.2f} characters per token)")
sample = "Hello! How can I help you today?"
print("example:", sample, "->", [tok.decode([i]) for i in tok.encode_ordinary(sample)])
