"""Capstone stage 1: build the pretraining corpus (the lesson 18 pipeline, condensed).

python data.py      -> data/documents.jsonl  (~3 MB of cleaned, deduplicated public-domain text)
"""
import hashlib
import json
import os
import unicodedata
import urllib.request

SOURCES = {
    "shakespeare": "https://raw.githubusercontent.com/karpathy/char-rnn/master/data/tinyshakespeare/input.txt",
    "pride_and_prejudice": "https://raw.githubusercontent.com/GITenberg/Pride-and-Prejudice_1342/master/1342.txt",
    "frankenstein": "https://raw.githubusercontent.com/GITenberg/Frankenstein_84/master/84.txt",
    "sherlock_holmes": "https://raw.githubusercontent.com/GITenberg/The-Adventures-of-Sherlock-Holmes_1661/master/1661.txt",
    "alice": "https://raw.githubusercontent.com/GITenberg/Alice-s-Adventures-in-Wonderland_11/master/11.txt",
    "tom_sawyer": "https://raw.githubusercontent.com/GITenberg/The-Adventures-of-Tom-Sawyer_74/master/74.txt",
}
os.makedirs("data/raw", exist_ok=True)


def clean(text):
    text = unicodedata.normalize("NFC", text).replace("\r\n", "\n").replace("\r", "\n")
    if "*** START OF" in text:                               # strip Project Gutenberg's header and licence
        text = text[text.find("\n", text.find("*** START OF")) + 1:]
    if "*** END OF" in text:
        text = text[:text.find("*** END OF")]
    return text


docs, seen = [], set()
for name, url in SOURCES.items():
    path = f"data/raw/{name}.txt"
    if not os.path.exists(path):
        urllib.request.urlretrieve(url, path)
    kept = 0
    for para in clean(open(path, encoding="utf-8", errors="replace").read()).split("\n\n"):
        para = "\n".join(line.rstrip() for line in para.strip("\n").split("\n"))
        letters = sum(ch.isalpha() for ch in para)
        if len(para) < 40 or letters < 0.6 * len(para) or "[Illustration" in para:
            continue                                         # quality filters
        fp = hashlib.sha256(" ".join(para.lower().split()).encode()).hexdigest()
        if fp in seen:
            continue                                         # exact duplicate
        seen.add(fp)
        split = "val" if int(fp[:8], 16) % 50 == 0 else "train"
        docs.append({"source": name, "split": split, "text": para})
        kept += 1
    print(f"{name:20s} {kept:6,} documents")

with open("data/documents.jsonl", "w", encoding="utf-8") as f:
    for d in docs:
        f.write(json.dumps(d) + "\n")
chars = sum(len(d["text"]) for d in docs)
print(f"total: {len(docs):,} documents, {chars:,} characters -> data/documents.jsonl")
