# 21 · What is an embedding?

**What you'll build:** a short program that turns sentences into lists of 384 numbers and shows that sentences with similar **meaning** get similar numbers, even when they share no words ("refund" vs "money back").
**Time:** ~30 min · **Builds on:** a working Python setup from [00 · Start here](../../00-start-here) · **Needs:** nothing extra (no API key, runs on your computer)

## Why this matters
Every "search by meaning" feature you have used (a help centre that understands your question, Spotify finding similar songs, ChatGPT reading your files) starts by turning things into embeddings. They are the foundation of RAG and vector databases, the rest of Part 5. AI engineers work with them every day.

## What you'll learn
- **Embedding:** a list of numbers that describes what a piece of text *means*.
- **Embedding model:** a small AI that reads text and writes out its embedding. You'll use a free one that runs on your own computer.
- **Cosine similarity:** a score from about 0 (unrelated) to 1 (same meaning) that compares two embeddings.
- **Meaning vs words:** two sentences can share no words and still be close in meaning, and the numbers show it.

## Before you start
- Install the Part 5 packages (once, inside your virtual environment):
  ```bash
  pip install chromadb numpy pypdf anthropic fastapi "uvicorn[standard]" python-multipart
  ```
  This lesson only uses two of them: `chromadb` (it contains the free embedding model) and `numpy` (fast maths on lists of numbers).
- No API key needed.

## Run it
1. Go to the course folder (`Learning/ai-from-zero`) and switch on your virtual environment.
2. Run:
   ```bash
   cd part-5-rag-and-vector-databases/21-what-is-an-embedding
   python embeddings.py
   ```
   The first run downloads the embedding model (about 80 MB, once). Later runs start in a few seconds.

### What you should see
```
'I love pizza' became 384 numbers. The first 6: [-0.099  0.034  0.01   0.053 -0.08   0.003]

0.87 ██████████████████████████     'I love pizza'  vs  'Pizza is my favourite food'
0.66 ███████████████████            'I love pizza'  vs  'I enjoy eating Italian food'
0.59 █████████████████              'How do I get a refund?'  vs  'I want my money back'
0.63 ██████████████████             'The cat sat on the mat'  vs  'A kitten was resting on the rug'
0.02                                'I love pizza'  vs  'The stock market fell today'
0.04 █                              'How do I get a refund?'  vs  'What's the weather tomorrow?'
```
Look at the third line: "refund" and "money back" share no words, yet they score 0.59. The last two pairs are unrelated and score close to 0. That gap is what makes search by meaning possible.

## How it works
An **embedding** is like GPS coordinates for meaning. GPS uses 2 numbers (latitude, longitude) to place you on a map; this model uses 384 numbers to place a sentence on a "map of meaning". Sentences about similar things land close together.

1. `embed = DefaultEmbeddingFunction()` loads the free model that comes with Chroma (it's called *all-MiniLM-L6-v2*). It runs on your computer, so it costs nothing.
2. `embed(["I love pizza"])` takes a **list** of texts and returns one embedding per text. `[0]` takes the first one. The program prints how many numbers it has (384) and the first 6.
3. `similarity(a, b)` embeds both sentences and compares them with **cosine similarity**: `np.dot(va, vb)` multiplies the two lists number by number and adds it all up, and dividing by the two lengths (`np.linalg.norm`) scales the result so it lands between -1 and 1. In practice, for this model, unrelated texts score near 0 and near-identical ones near 1.
4. The `for a, b in pairs:` loop prints each score with a bar (`'█' * int(score * 30)`) so you can see the differences at a glance.

```
"I love pizza" ──► embedding model ──► [-0.099, 0.034, 0.010, ... 384 numbers]
                                                │
"Pizza is my favourite food" ──► ... ──► [...] ─┴─► cosine similarity ──► 0.87
```

## If something goes wrong
- **`ModuleNotFoundError: No module named 'chromadb'`** → your virtual environment is off, or you skipped the install. Switch it on (`source .venv/bin/activate` on Mac, `.venv\Scripts\activate` on Windows) and run the `pip install` line again.
- **The first run hangs for a minute, or fails with a download/connection error** → it is downloading the model. Check your internet connection and run it again; it resumes. Once downloaded it lives in a `.cache/chroma` folder in your home folder and never downloads again.
- **`pip install chromadb` fails with `No matching distribution found for onnxruntime`** (or another package) → your Python is too new or too old for one of Chroma's parts. Check with `python --version`; Python 3.11, 3.12 or 3.13 work well. Install one of those from python.org, make a fresh venv, and install again.
- **Your scores are a tiny bit different (0.86 instead of 0.87)** → normal. Different computers round numbers slightly differently.

## Try this
1. Add your own pairs to the `pairs` list, then run it again. Try two sentences you think mean the same thing.
2. Add `("I love pizza", "I hate pizza")`. Do you expect a high or a low score? Run it and see.
   <details><summary>Hint</summary>

   It scores about 0.81: high! Both sentences are about *your feelings towards pizza*, so they sit close on the map, even though they disagree. Embeddings capture the **topic** much more than "yes vs no". Keep this in mind when you build search: it finds related text, not necessarily text that agrees.
   </details>
3. Find out how well this model handles other languages: add `("I love dogs", "J'adore les chiens")` and `("The bank of the river", "The bank approved my loan")`.
   <details><summary>Hint</summary>

   The French pair scores only about 0.25, because this small model was trained mostly on English. (Bigger "multilingual" models score translations very high.) The two "bank" sentences score about 0.35: they share a word but not a meaning, so the score stays low-ish. A model is a tool with limits, so always test it on your own kind of text.
   </details>

## Check yourself
1. In your own words, what is an embedding?
2. Why can't you find "I want my money back" by searching for the word "refund"? How do embeddings solve that?
3. Two texts get a cosine similarity of 0.03. What does that tell you?
4. Does a high score mean two sentences agree with each other?

<details><summary>Answers</summary>

1. A list of numbers (here 384) that describes what a text means, so that texts with similar meanings get similar numbers.
2. The words are different, so a word search finds nothing. Embeddings compare meanings instead of letters, so "refund" and "money back" land close together.
3. They are about unrelated things.
4. No. It means they are about the same topic. "I love pizza" and "I hate pizza" score high.
</details>

## Learn more (optional)
- Video search: [what are word embeddings](https://www.youtube.com/results?search_query=what+are+embeddings+explained+simply)
- The model you just used: [all-MiniLM-L6-v2](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2)

## Next
→ [22 · Search by meaning](../22-search-by-meaning)
