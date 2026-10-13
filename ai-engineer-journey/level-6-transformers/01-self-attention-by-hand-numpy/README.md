# 6.1 · Self-attention by hand (NumPy)

**What you build:** one attention head, step by step: queries, keys and values, the score table, the causal mask, softmax, and the weighted mix. Then two heads combined into **multi-head attention**.
**Like you're 10:** a classroom where every word holds up a sign saying what it's looking for ("I'm a verb, who's doing me?") and wears a badge saying what it is ("I'm a noun, an animal"). Words with matching signs and badges listen to each other more. In a GPT you may only listen to classmates who spoke *before* you.

## Run it
```bash
cd level-6-transformers/01-self-attention-by-hand-numpy
pip install -r requirements.txt
python attention.py
```
You'll see the 6×6 attention table for "the cat sat on the mat", with zeros above the diagonal (the causal mask).

## The formula (now you can read it!)
```
Attention(Q, K, V) = softmax( Q·Kᵀ / √d  + mask ) · V
```
| Piece | Plain English |
|-------|---------------|
| `Q = X·Wq` | what each word is looking for |
| `K = X·Wk` | what each word offers to be found by |
| `V = X·Wv` | the information each word passes along |
| `Q·Kᵀ` | match score for every pair of words |
| `/ √d` | keeps scores from getting too big |
| mask | no peeking at future words (GPT-style "causal" attention) |
| softmax | turns scores into weights that sum to 1 |
| `· V` | each word becomes a weighted blend of the words it attends to |

## Your turn
1. Remove the mask. That's how **BERT** (5.5) attends: both directions.
2. Make "sat" attend strongly to "cat" by hand-editing `Wq`/`Wk` so their query and key align.
3. Write `attention()` as a function that handles a batch: `X` with shape `(B, T, d)`.

## Watch
- Attention in transformers, step-by-step (3Blue1Brown): https://www.youtube.com/results?search_query=3blue1brown+attention+in+transformers+step+by+step
- The Illustrated Transformer (Jay Alammar, blog): https://jalammar.github.io/illustrated-transformer/
