# 6.1 · Self-attention by hand (NumPy)

**What you'll build:** one attention head, step by step (queries, keys, values, the score table, the causal mask, softmax and the weighted mix), then two heads combined into **multi-head attention**. About 60 lines of NumPy, no deep-learning library.
**Like you're 10:** a classroom where every word holds up a sign saying what it's looking for ("I'm a verb, who's doing me?") and wears a badge saying what it is ("I'm a noun, an animal"). Words whose signs match other words' badges listen to those words more. In a GPT you may only listen to classmates who spoke *before* you.
**Time:** ~1.5 h · **Builds on:** [5.6 BPE tokenizer from scratch](../../level-5-text-models/06-bpe-tokenizer-from-scratch) · **Needs:** nothing extra (runs on any laptop in under a second)

## Why this matters
Attention is the one idea every modern language model is built on. GPT, Claude, Llama and BERT are all stacks of the block you write here, repeated dozens of times. When people talk about "context windows", "KV caches" or "long-context cost", they are talking about the score table you build in this lesson. Once you have computed it by hand, transformer papers and diagrams stop looking like magic.

## What you'll learn
- **Query, key, value (Q, K, V)**: three small matrix multiplications that turn each word into "what I'm looking for", "what I offer" and "what I pass along".
- **Attention scores**: a table where row *i*, column *j* says how well word *i*'s query matches word *j*'s key.
- **Causal mask**: hiding future words so a GPT can't cheat by peeking at the word it is meant to predict.
- **Softmax**: turning a row of scores into weights that are all positive and add up to 1.
- **Multi-head attention**: running several small attention heads side by side and gluing their answers back together.

## Before you start
```bash
cd level-6-transformers/01-self-attention-by-hand-numpy
pip install -r requirements.txt
```
- `numpy`: fast maths on arrays (matrices). That's the only package.
- No API key needed. No GPU needed.

## Run it
1. From the course root, go to the folder: `cd level-6-transformers/01-self-attention-by-hand-numpy`
2. Run the script: `python attention.py`

### What you should see
```
Attention weights (row = word looking, column = word looked at):
           the   cat   sat    on   the   mat
   the    1.00  0.00  0.00  0.00  0.00  0.00
   cat    0.46  0.54  0.00  0.00  0.00  0.00
   sat    0.32  0.23  0.45  0.00  0.00  0.00
    on    0.20  0.65  0.11  0.03  0.00  0.00
   the    0.03  0.03  0.60  0.31  0.03  0.00
   mat    0.19  0.45  0.02  0.04  0.19  0.10

Notice: the upper triangle is 0 (no peeking at the future), and every row sums to 1.
output shape: (6, 4) -> each word now carries context from the words before it
multi-head output shape: (6, 8) (same as input, so blocks can be stacked)
```
What to look at:
- **Everything above the diagonal is 0.00.** That's the causal mask: "cat" can't see "sat", "on", "the", "mat" yet.
- **The first row is 1.00 then zeros.** The first word has nobody to look at except itself.
- **Each row adds up to 1** (check one: 0.32 + 0.23 + 0.45 = 1.00). Softmax did that.
- The numbers come from random weights (seeded, so you get exactly these). In a trained model (6.2) the pattern would mean something, for example "sat" looking hard at "cat" to find out *who* sat.

## How it works
The formula you are implementing, from the 2017 paper *Attention Is All You Need*:
```
Attention(Q, K, V) = softmax( Q·Kᵀ / √d  + mask ) · V
```

```
words ─► embeddings X (6×8)
            │
            ├─ X·Wq ─► Q (6×4)  "what am I looking for?"
            ├─ X·Wk ─► K (6×4)  "what do I contain?"
            └─ X·Wv ─► V (6×4)  "what do I pass along?"

Q·Kᵀ/√d ─► scores (6×6) ─► mask future ─► softmax ─► weights (6×6)
weights · V ─► out (6×4): each word = a blend of the words it attended to
```

1. **Embeddings.** `emb_table` gives every distinct word a random vector of `d_model = 8` numbers, and `X` stacks them into a 6×8 matrix (one row per word). Both "the"s share the same row because they're the same word. In a real model these vectors are learned during training. `sorted(set(words))` keeps the order fixed so your output matches the one above.
2. **Projections.** `Wq`, `Wk`, `Wv` are 8×4 matrices of random numbers. Multiplying `X @ Wq` gives `Q`: one 4-number "question" per word. Same for `K` (keys) and `V` (values). These three matrices are what training adjusts.
3. **Scores.** `scores = Q @ K.T / np.sqrt(d_head)` dots every query with every key, giving a 6×6 table. A big dot product means "your badge matches my sign". Dividing by √4 = 2 keeps the numbers small; without it, softmax tends to put almost all the weight on one word (try it in *Try this*).
4. **Causal mask.** `np.triu(..., k=1)` marks every cell above the diagonal. Setting those to `-np.inf` means "infinitely bad match", and softmax turns that into exactly 0.
5. **Softmax.** `softmax()` exponentiates each score and divides by the row total, so each row becomes a set of positive weights that add to 1. Subtracting the row's max first (`z - z.max(...)`) stops `exp()` overflowing; it doesn't change the answer.
6. **Mix the values.** `out = weights @ V` replaces each word with a weighted average of the value vectors it attended to. That's how "mat" picks up information about "cat" and "sat".
7. **Multi-head.** `attention_head()` repeats steps 2–5 with fresh random weights. Two heads run side by side, their 4-wide outputs are glued into 8 columns (`np.concatenate`) and mixed by `Wo`. The result is 6×8, the same shape as `X`, so you can stack another attention block on top. Real models use 12–100+ heads, each free to learn a different kind of relationship (grammar, who-did-what, nearby words).

One thing attention does **not** know is word order: without the mask, the two "the" rows would be identical. That's why GPT adds *position embeddings*, which you'll see in 6.2.

## If something goes wrong
- **`ModuleNotFoundError: No module named 'numpy'`** → activate your virtual environment (Level 0.1) and run `pip install -r requirements.txt` again.
- **`python: can't open file 'attention.py'`** → you're in the wrong folder. Run the `cd` line from the course root first.
- **Your numbers differ from the README** → you changed the seed, `d_model`/`d_head`, or the word list. Any change to the random draws changes every number. The patterns (zeros above the diagonal, rows summing to 1) should still hold.
- **`RuntimeWarning: invalid value encountered`** after editing → a whole row got masked to `-inf` (for example if you used `k=0` in `np.triu`, which hides each word from itself too). Every row needs at least one visible word.

## Try this
1. **Turn off the mask (BERT-style attention).** Comment out the line `scores[mask] = -np.inf` and run again. What happens to the upper triangle? Compare the two "the" rows.
   <details><summary>Hint</summary>

   Every word now sees every other word, in both directions, which is how BERT (5.5) reads. The two "the" rows become identical (`0.02 0.02 0.38 0.20 0.02 0.37`), because they have the same embedding and attention alone has no idea which one came first. This is exactly why transformers need position information.
   </details>
2. **Remove the √d scaling.** Change the scores line to `scores = Q @ K.T` and run. Are the rows more spread out or more "spiky"?
   <details><summary>Hint</summary>

   Spikier. For example the "on" row goes from `0.20 0.65 0.11 0.03` to `0.08 0.89 0.03 0.00`. Bigger scores make softmax pick one winner. With large `d_head` (64 or 128 in real models) this gets extreme and training struggles, so the scaling matters.
   </details>
3. **Write a batched `attention()` function** that takes `X` with shape `(B, T, d)` (B sentences at once) plus `Wq, Wk, Wv`, and returns `(B, T, d_head)`.
   <details><summary>Solution</summary>

   ```python
   def attention(X, Wq, Wk, Wv, causal=True):
       Q, K, V = X @ Wq, X @ Wk, X @ Wv                           # each (B, T, d_head)
       scores = Q @ K.transpose(0, 2, 1) / np.sqrt(Q.shape[-1])   # (B, T, T)
       if causal:
           T = X.shape[1]
           future = np.triu(np.ones((T, T), dtype=bool), k=1)
           scores = np.where(future, -np.inf, scores)             # same mask for every sentence
       return softmax(scores) @ V                                 # (B, T, d_head)

   X = rng.normal(size=(3, 6, 8))
   print(attention(X, Wq, Wk, Wv).shape)   # (3, 6, 4)
   ```
   `K.transpose(0, 2, 1)` swaps the last two axes of each sentence's keys, which is `K.T` done per sentence. This is the same shape juggling PyTorch does in 6.2.
   </details>

## Check yourself
1. What's the difference between a key and a value?
2. Why is the first row of the table always `1.00 0.00 0.00 ...` when the mask is on?
3. If a sentence has 1,000 tokens instead of 6, how big is the score table? Why does that make long prompts expensive?
4. Why does the multi-head output need to have the same shape as the input?

<details><summary>Answers</summary>

1. The key is used only to *decide* how much attention a word gets (it's matched against queries). The value is the information that actually gets *passed along* once the weights are decided.
2. The first word may only look at itself (everything after it is masked), and softmax over one visible number gives 1.0.
3. 1,000 × 1,000 = 1,000,000 scores, per head, per layer. The table grows with the square of the length, so doubling the prompt roughly quadruples this part of the work.
4. So you can stack blocks: the output of one attention layer becomes the input `X` of the next. GPT-style models stack dozens.
</details>

## Learn more (optional)
- Attention in transformers, step-by-step (3Blue1Brown): https://www.youtube.com/results?search_query=3blue1brown+attention+in+transformers+step+by+step
- The Illustrated Transformer (Jay Alammar, blog): https://jalammar.github.io/illustrated-transformer/

## Next
→ [6.2 · Mini-GPT trained on Shakespeare](../02-mini-gpt-trained-on-shakespeare)
