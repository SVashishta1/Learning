# 5.6 · BPE tokenizer from scratch

**What you build:** a **Byte-Pair Encoding** tokenizer, the same algorithm family GPT models use. You train it on a paragraph, watch it learn merges like `"t" + "h" → "th"` and then `"th" + "e" → "the"`, and check that `decode(encode(text)) == text`, emoji included.
**Like you're 10:** you're texting and get tired of typing "t-h-e" every time, so you invent a shortcut key for "the". Then for "ing". Then for "token". BPE invents the shortcuts that save the most typing, automatically.

## Run it
```bash
cd level-5-text-models/06-bpe-tokenizer-from-scratch
python bpe.py
pip install tiktoken && python bpe.py     # optional: compare with a real GPT tokenizer
```

## Key ideas
- **Tokens, not words:** LLMs read token ids. 1 token ≈ ¾ of an English word on average.
- **Byte-level:** starting from the 256 possible bytes means *any* text works (emoji, Hindi, code), with no "unknown word" problems.
- **Merges are learned once** from a big text sample, then frozen. Model and tokenizer are a matched pair.
- **This explains LLM quirks:** why they can miscount the letters in "strawberry" (they see tokens, not letters), why API pricing is per token, and why the context window is measured in tokens.

## Your turn
1. Train on a Python file instead of English. What merges appear? (Hint: indentation spaces.)
2. Add GPT-style **pre-splitting** with a regex so merges never cross word boundaries. Karpathy's video shows how.
3. Encode the same sentence in English and in another language. Which needs more tokens? What does that mean for API cost?

## Watch
- Let's build the GPT Tokenizer (Karpathy): https://www.youtube.com/results?search_query=karpathy+let%27s+build+the+GPT+tokenizer
- Karpathy's minbpe repo: https://github.com/karpathy/minbpe
