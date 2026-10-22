# 5.6 · BPE tokenizer from scratch

**What you'll build:** a **Byte-Pair Encoding** (BPE) tokenizer, the same algorithm family GPT models use. You train it on a paragraph, watch it learn merges like `"e" + " " → "e "` and `" t" + "h" → " th"`, and check that `decode(encode(text)) == text`, emoji included.
**Like you're 10:** you're texting and get tired of typing "t-h-e" every time, so you invent a shortcut key for "the". Then for "ing". Then for "token". BPE invents the shortcuts that save the most typing, automatically.
**Time:** ~2 h · **Builds on:** [5.5 DistilBERT](../05-sentiment-with-pretrained-distilbert) (where you saw `un ##bel ##ie ##va ##bly`) and [5.2 bigrams](../02-next-letter-predictor-bigram-name-generator) (counting pairs) · **Needs:** nothing extra (optional: `tiktoken` + internet to compare with GPT's tokenizer)

## Why this matters
Every LLM reads and writes **tokens**, not letters or words, and the tokenizer decides what those tokens are. It explains things you'll meet daily as an AI engineer: API prices are per token, context windows are measured in tokens, some languages cost more than others, and models can stumble on spelling or counting letters ("how many r's in strawberry?") because they never see the letters. Building one yourself takes away the mystery.

## What you'll learn
- **Tokens, not words**: LLMs read token ids. In English, 1 token is about ¾ of a word on average.
- **Byte-level start**: beginning from the 256 possible bytes means *any* text works (emoji, Hindi, code), with no "unknown word" problems.
- **The BPE training loop**: count neighbouring pairs, merge the most frequent one into a new token, repeat.
- **Encoding and decoding**: applying the learned merges in order, and turning ids back into exact text.
- **Merges are learned once, then frozen**: a model and its tokenizer are a matched pair.

## Before you start
No packages needed: `bpe.py` is pure Python. `requirements.txt` only lists the optional extra.

Optional, to compare with a real GPT tokenizer:
```bash
pip install tiktoken
```
- `tiktoken`: OpenAI's fast tokenizer library. The first time, it downloads the `cl100k_base` vocabulary (~1.7 MB), so it needs internet once.

No API key needed. The training text is `training_text.txt` (one paragraph about tokenizers, ~1,200 characters).

## Run it
1. From the course root:
   ```bash
   cd level-5-text-models/06-bpe-tokenizer-from-scratch
   ```
2. Train the tokenizer and test it:
   ```bash
   python bpe.py
   ```
3. Optional, with the GPT comparison:
   ```bash
   pip install tiktoken
   python bpe.py
   ```

### What you should see
```
merge # 1: b'e' + b' ' -> b'e '  (seen 43x)
merge # 2: b' ' + b't' -> b' t'  (seen 33x)
merge # 3: b'e' + b'r' -> b'er'  (seen 27x)
merge # 4: b'e' + b'n' -> b'en'  (seen 23x)
merge # 5: b's' + b' ' -> b's '  (seen 23x)
merge # 6: b'a' + b'n' -> b'an'  (seen 22x)
merge # 7: b' t' + b'h' -> b' th'  (seen 21x)
merge # 8: b'i' + b'n' -> b'in'  (seen 18x)
merge # 9: b't' + b' ' -> b't '  (seen 16x)
merge #10: b'y' + b' ' -> b'y '  (seen 15x)

'The tokenizer learns that common words are worth a single token. 🤖'
-> 69 bytes became 27 tokens
pieces: ['Th', 'e tokenizer ', 'le', 'ar', 'n', 's', ' th', 'a', 't ', 'com', 'mon ', 'words ', 'ar', 'e ', 'wor', 'th', ' ', 'a ', 's', 'ing', 'le t', 'oken', '. ', '�', '�', '�', '�']
(the 4 '�' pieces are the emoji's 4 bytes: one byte alone isn't valid text, but together they decode fine)
✅ decode(encode(text)) == text

(pip install tiktoken to compare with a real GPT tokenizer)
```
With `tiktoken` installed and online, the last line instead shows GPT-4's tokenizer splitting the same sentence into about 15 tokens, nearly one per word (e.g. `' tokenizer'`, `' common'`, `' words'`).

What to look at:
- **The merges**: the first ones are the most common pairs in English: "e" at the end of a word, " t" at the start, "er", "th".
- **69 bytes → 27 tokens**: frequent chunks became single tokens, so the text got 2.5× shorter.
- **Odd pieces like `'e tokenizer '`**: with only one paragraph of training text, the tokenizer learns that paragraph's favourite phrases. Real tokenizers train on gigabytes, so their tokens are much more general. (Try this 2 shows the trick GPT uses to stop merges crossing word boundaries.)
- **The emoji** stays as 4 raw bytes, because it never appeared in the training text, but the round trip still works.

## How it works
```
"the cat"  ─encode('utf-8')─►  [116, 104, 101, 32, 99, 97, 116]   (7 bytes, ids 0-255)
                                  └─┬──┘
           merge (116,104) → 256  ("th" was the most common pair)
                               [256, 101, 32, 99, 97, 116]
           merge (256,101) → 257  ("th"+"e")
                               [257, 32, 99, 97, 116]              ...and so on, up to vocab_size
```
1. **Start from bytes.** `text.encode("utf-8")` turns any text into bytes (numbers 0–255). English letters are 1 byte each; "é" is 2; most emoji are 4. `self.vocab` starts with those 256 single bytes, so *any* text can be encoded, with no "unknown word" token ever needed.
2. **`_pairs(ids)`** counts every neighbouring pair with `Counter(zip(ids, ids[1:]))`. Same counting as the bigrams in 5.2, but on bytes.
3. **`_merge(ids, pair, new_id)`** walks through the list and replaces every occurrence of the pair with the single new id.
4. **`train(text, vocab_size)`** repeats: count pairs → take the most frequent (`max(pairs, key=pairs.get)`) → merge it everywhere → record it. `self.merges[pair] = new_id` remembers the rule (in learning order); `self.vocab[new_id]` stores which bytes the new token stands for (the two parts glued together). With `vocab_size=400` it learns 144 merges (ids 256–399). `verbose=True` prints the first 10.
5. **`encode(text)`** turns new text into ids: start from bytes, then repeatedly find the pair in the text whose merge was learned **earliest** (lowest id, via `min(..., key=self.merges.get)`), and apply it. Order matters, because later merges are built from earlier ones ("th" must exist before "the"). Stop when no learned merge applies.
6. **`decode(ids)`** looks up each id's bytes, joins them, and decodes the UTF-8. A single emoji byte isn't valid text alone (shown as `�` when printed separately), but all four together decode back to 🤖.
7. **The main block** trains on `training_text.txt`, encodes a sample sentence, prints the pieces, checks the round trip with `assert`, and, if `tiktoken` is installed, compares with GPT-4's `cl100k_base` tokenizer (100,000 tokens trained on a huge amount of text).

## If something goes wrong
- **`FileNotFoundError: ... training_text.txt`** → the text file must be in the same folder as `bpe.py`.
- **`(tiktoken couldn't download its vocabulary ...)`** → tiktoken is installed but offline or blocked. Try another network; after one download it's cached.
- **`UnicodeDecodeError`** (when you train on your own file) → open it with `encoding="utf-8"` (the script already does for `training_text.txt`), or save your file as UTF-8.
- **Training on a big file is very slow** → this simple version recounts every pair after every merge. It's fine for a few hundred KB; real tokenizers use cleverer bookkeeping (see Karpathy's `minbpe` in Learn more).
- **`AssertionError: round trip failed!`** (after you edited the code) → usually `encode` applies merges in the wrong order, or `vocab` wasn't updated for a merge. Compare with the original `train` and `encode`.

## Try this
1. **Tokenize code.** Train on a Python file instead of English. What merges appear first?
   <details><summary>Hint</summary>

   In the main block, change the training text to `text = open(__file__, encoding="utf-8").read()` (the script trains on itself). The first merges become `'  '`, `'    '`, `'        '` and `'\n        '`: indentation! Code is full of runs of spaces, so a tokenizer trained on code saves a lot on them. That's why code-focused models use tokenizers trained on code.
   </details>
2. **Don't merge across words.** Add GPT-style **pre-splitting**: first split the text into chunks with a regular expression (words with their leading space, punctuation, whitespace), and only merge *inside* chunks.
   <details><summary>Solution</summary>

   Add below the `BPETokenizer` class:
   ```python
   import re
   SPLIT = re.compile(r" ?\w+| ?[^\w\s]+|\s+")   # " word", " ,", spaces: merges can't cross these


   class SplitBPE(BPETokenizer):
       def train(self, text, vocab_size, verbose=False):
           chunks = [list(c.encode("utf-8")) for c in SPLIT.findall(text)]
           for new_id in range(256, vocab_size):
               pairs = Counter()
               for ids in chunks:                     # count pairs inside each chunk only
                   pairs.update(self._pairs(ids))
               if not pairs:
                   break
               pair = max(pairs, key=pairs.get)
               chunks = [self._merge(ids, pair, new_id) for ids in chunks]
               self.merges[pair] = new_id
               self.vocab[new_id] = self.vocab[pair[0]] + self.vocab[pair[1]]
           return self

       def encode(self, text):
           return [i for chunk in SPLIT.findall(text) for i in super().encode(chunk)]
   ```
   and use `SplitBPE()` instead of `BPETokenizer()` in the main block. Now the pieces look like real word parts (`' tokenizer'`, `' words'`, `' single'`, `' token'`) instead of `'e tokenizer '`. GPT's real pattern is fancier (it handles "'s", numbers and Unicode letters), and Karpathy's video builds it step by step.
   </details>
3. **The language tax.** Encode the same sentence in English and in another language with your tokenizer. Which needs more tokens? What would that mean for API costs?
   <details><summary>Hint</summary>

   Add at the end of the main block:
   ```python
   for t in ["The tokenizer is the first step of every language model.",
             "El tokenizador es el primer paso de todo modelo de lenguaje.",
             "टोकनाइज़र हर भाषा मॉडल का पहला कदम है।"]:
       print(len(t.encode()), "bytes ->", len(tok.encode(t)), "tokens |", t)
   ```
   English: 16 tokens; Spanish: 36; Hindi: 100 (every byte is its own token, and each Devanagari letter is 3 bytes). Same meaning, 6× the tokens, so 6× the price and 6× less fits in the context window. Real tokenizers are trained on many languages to reduce this gap, but it hasn't disappeared.
   </details>

## Check yourself
1. Why does BPE start from bytes instead of from a list of words?
2. Why must `encode` apply merges in the order they were learned?
3. Why might an LLM miscount the letters in "strawberry"?
4. Why must a model always be used with the exact tokenizer it was trained with?

<details><summary>Answers</summary>

1. Any text in any language (and emoji, code, typos) is made of bytes, so nothing is ever "unknown". A word list would always miss some words.
2. Later merges are built from tokens created by earlier merges. Applying a later merge first could miss pairs that only exist after an earlier merge, giving different (and longer) token sequences than training produced.
3. It sees a few multi-letter chunks (something like "str" + "aw" + "berry"), not individual letters, so counting letters requires knowledge it never directly observes.
4. The model learned what each token id *means*. A different tokenizer would give different ids for the same text, so the model would read nonsense.
</details>

## Learn more (optional)
- Let's build the GPT Tokenizer (Karpathy): https://www.youtube.com/watch?v=zduSFxRajkE
- Karpathy's minbpe repo: https://github.com/karpathy/minbpe
- See how GPT tokenizes your own text: https://platform.openai.com/tokenizer

## Next
You've finished Level 5! Next, the model that made all of this famous:
→ [Level 6 · 6.1 Self-attention by hand (NumPy)](../../level-6-transformers/01-self-attention-by-hand-numpy)
