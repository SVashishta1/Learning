"""Lesson 18: a small but complete pretraining-data pipeline.

    download -> clean -> split into documents -> quality filter -> exact dedup -> near dedup (MinHash)
    -> train/val split -> tokenize (GPT-2 BPE) -> write binary shards

python pipeline.py                       # ~4 MB of public-domain text from GitHub, ~1 minute
python pipeline.py --shard-size 100000   # smaller shards (more files)
Output: data/shards/*.bin, readable by dataloader.py here and by lesson 15's train_gpt2.py --data data/shards
"""
import argparse
import json
import os
import time
import unicodedata
import urllib.request

import numpy as np

from dedup import MinHasher, estimated_jaccard, fingerprint, jaccard, lsh_candidates, shingles

# Public-domain texts hosted on GitHub. Two are deliberate traps:
#  * tinyshakespeare appears twice (two repos host the identical file) -> exact duplicates
#  * Alice appears twice (two different editions, lightly edited)     -> near duplicates
SOURCES = {
    "shakespeare": "https://raw.githubusercontent.com/karpathy/char-rnn/master/data/tinyshakespeare/input.txt",
    "shakespeare_copy": "https://raw.githubusercontent.com/jcjohnson/torch-rnn/master/data/tiny-shakespeare.txt",
    "pride_and_prejudice": "https://raw.githubusercontent.com/GITenberg/Pride-and-Prejudice_1342/master/1342.txt",
    "frankenstein": "https://raw.githubusercontent.com/GITenberg/Frankenstein_84/master/84.txt",
    "sherlock_holmes": "https://raw.githubusercontent.com/GITenberg/The-Adventures-of-Sherlock-Holmes_1661/master/1661.txt",
    "alice": "https://raw.githubusercontent.com/GITenberg/Alice-s-Adventures-in-Wonderland_11/master/11.txt",
    "alice_1916_edition": "https://raw.githubusercontent.com/GITenberg/Alice-s-Adventures-in-Wonderland_19033/master/19033.txt",
}
MAGIC, VERSION = 20240520, 1          # shard header (same layout as Karpathy's llm.c)

p = argparse.ArgumentParser()
p.add_argument("--out", default="data")
p.add_argument("--min-chars", type=int, default=40, help="drop documents shorter than this")
p.add_argument("--near-dup-threshold", type=float, default=0.5, help="estimated Jaccard above which two docs are near-duplicates")
p.add_argument("--shard-size", type=int, default=250_000, help="tokens per shard file")
args = p.parse_args()
for sub in ("raw", "shards"):
    os.makedirs(os.path.join(args.out, sub), exist_ok=True)
t_start = time.time()


def step(title):
    print(f"\n[{time.time() - t_start:5.1f}s] {title}")


# ----------------------------------------------------------------------------- 1. download
step("1. download")
raw = {}
for name, url in SOURCES.items():
    path = os.path.join(args.out, "raw", name + ".txt")
    if not os.path.exists(path):
        urllib.request.urlretrieve(url, path)
    raw[name] = open(path, encoding="utf-8", errors="replace").read()
    print(f"   {name:22s} {len(raw[name]):>10,} characters")


# ----------------------------------------------------------------------------- 2. clean
def clean(text):
    text = unicodedata.normalize("NFC", text)               # one standard form for accented letters
    text = text.replace("\r\n", "\n").replace("\r", "\n")   # Windows/old-Mac line endings -> "\n"
    start = text.find("*** START OF")                        # Project Gutenberg wraps every book in a licence:
    if start != -1:                                          # keep only what is between the START and END markers
        text = text[text.find("\n", start) + 1:]
    end = text.find("*** END OF")
    if end != -1:
        text = text[:end]
    return text


step("2. clean (unicode, line endings, Project Gutenberg header/footer)")
cleaned = {name: clean(t) for name, t in raw.items()}
for name in cleaned:
    print(f"   {name:22s} {len(raw[name]):>10,} -> {len(cleaned[name]):>10,} characters")

# ----------------------------------------------------------------------------- 3. documents
step("3. split into documents (one paragraph = one document)")
docs = []
for name, text in cleaned.items():
    for para in text.split("\n\n"):                          # paragraphs are separated by a blank line
        para = "\n".join(line.rstrip() for line in para.strip("\n").split("\n"))
        if para.strip():
            docs.append({"source": name, "text": para})
print(f"   {len(docs):,} documents")


# ----------------------------------------------------------------------------- 4. quality filters
def quality_problem(text):
    """Return why a document is low quality, or None. Real pipelines (C4, Gopher, FineWeb) use dozens of such rules."""
    if len(text) < args.min_chars:
        return "too short"
    letters = sum(ch.isalpha() for ch in text)
    if letters / len(text) < 0.6:
        return "too few letters"                             # tables, numbers, decorations
    if "[Illustration" in text:
        return "illustration marker"
    if sum(ch.isupper() for ch in text) > 0.5 * letters:
        return "mostly CAPITALS"                             # title pages, chapter headings
    return None


step("4. quality filters")
reasons = {}
kept = []
for d in docs:
    r = quality_problem(d["text"])
    if r:
        reasons[r] = reasons.get(r, 0) + 1
    else:
        kept.append(d)
for r, n in sorted(reasons.items(), key=lambda kv: -kv[1]):
    print(f"   removed {n:6,} ({r})")
print(f"   kept {len(kept):,} of {len(docs):,}")
docs = kept

# ----------------------------------------------------------------------------- 5. exact dedup
step("5. exact deduplication (SHA-256 of normalised text)")
seen, kept, removed_by_source = set(), [], {}
for d in docs:
    fp = fingerprint(d["text"])
    if fp in seen:
        removed_by_source[d["source"]] = removed_by_source.get(d["source"], 0) + 1
    else:
        seen.add(fp)
        kept.append(d)
for src, n in sorted(removed_by_source.items(), key=lambda kv: -kv[1]):
    print(f"   removed {n:6,} exact duplicates from {src}")
docs = kept

# ----------------------------------------------------------------------------- 6. near dedup
step("6. near-duplicate removal (5-word shingles, MinHash with 128 hashes, LSH with 32 bands)")
mh = MinHasher(num_perm=128)
shingle_sets = [shingles(d["text"]) for d in docs]
sigs = [mh.signature(s) for s in shingle_sets]
candidates = lsh_candidates(sigs, bands=32)
drop, examples = set(), []
for i, j in sorted(candidates):
    est = estimated_jaccard(sigs[i], sigs[j])
    if est >= args.near_dup_threshold and i not in drop:
        drop.add(j)                                          # keep the first, drop the later one
        examples.append((est, jaccard(shingle_sets[i], shingle_sets[j]), i, j))
by_source = {}
for j in drop:
    by_source[docs[j]["source"]] = by_source.get(docs[j]["source"], 0) + 1
print(f"   {len(candidates):,} candidate pairs from LSH (instead of {len(docs) * (len(docs) - 1) // 2:,} all-pairs comparisons)")
for src, n in sorted(by_source.items(), key=lambda kv: -kv[1]):
    print(f"   removed {n:6,} near duplicates from {src}")
if examples:
    est, true, i, j = sorted(examples)[len(examples) // 2]   # a typical (median) example
    print(f"   example pair, estimated Jaccard {est:.2f}, true {true:.2f}:")
    print(f"     [{docs[i]['source']}] {docs[i]['text'][:110]!r}")
    print(f"     [{docs[j]['source']}] {docs[j]['text'][:110]!r}")
docs = [d for k, d in enumerate(docs) if k not in drop]
print(f"   {len(docs):,} documents left")

# ----------------------------------------------------------------------------- 7. split
step("7. train/val split (2% of documents, chosen by fingerprint so it never changes between runs)")
for d in docs:
    d["split"] = "val" if int(fingerprint(d["text"])[:8], 16) % 50 == 0 else "train"
with open(os.path.join(args.out, "documents.jsonl"), "w", encoding="utf-8") as f:
    for d in docs:
        f.write(json.dumps(d) + "\n")                        # one JSON object per line: easy to inspect and stream
print(f"   train {sum(d['split'] == 'train' for d in docs):,} | val {sum(d['split'] == 'val' for d in docs):,} "
      f"| saved {args.out}/documents.jsonl")

# ----------------------------------------------------------------------------- 8. tokenize + shards
step("8. tokenize with GPT-2's BPE (tiktoken) and write binary shards")
import tiktoken                                              # noqa: E402  (imported here so steps 1-7 work without it)

enc = tiktoken.get_encoding("gpt2")
EOT = enc.eot_token                                          # <|endoftext|> = 50256: marks where a document starts


def write_shard(split, index, tokens):
    path = os.path.join(args.out, "shards", f"corpus_{split}_{index:06d}.bin")
    header = np.zeros(256, dtype=np.int32)
    header[0], header[1], header[2] = MAGIC, VERSION, len(tokens)
    with open(path, "wb") as f:
        f.write(header.tobytes())                            # 1,024 bytes of header...
        f.write(np.array(tokens, dtype=np.uint16).tobytes())   # ...then 2 bytes per token (all ids < 65,536)
    print(f"   wrote {path}  ({len(tokens):,} tokens, {os.path.getsize(path) / 1e6:.2f} MB)")


shard_dir = os.path.join(args.out, "shards")
for old in os.listdir(shard_dir):                            # remove shards from an earlier run
    os.remove(os.path.join(shard_dir, old))
total_chars = 0
for split in ("val", "train"):
    buf, index = [], 0
    for d in docs:
        if d["split"] != split:
            continue
        buf.append(EOT)
        buf.extend(enc.encode_ordinary(d["text"]))
        total_chars += len(d["text"])
        while len(buf) >= args.shard_size:                   # shard full: write it, keep the rest
            write_shard(split, index, buf[:args.shard_size])
            buf, index = buf[args.shard_size:], index + 1
    if buf:
        write_shard(split, index, buf)
total_tokens = sum((os.path.getsize(os.path.join(shard_dir, f)) - 1024) // 2 for f in os.listdir(shard_dir))
step(f"done: {total_chars:,} characters -> {total_tokens:,} tokens ({total_chars / total_tokens:.2f} characters per token)")
