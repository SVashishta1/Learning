# 5.4 · Embeddings: find similar words and sentences

**What you'll build:**
- **Part A:** word vectors from scratch (co-occurrence counts + SVD). The model discovers that "apple" is like "banana" and "paris" is like "rome", without being told.
- **Part B:** a **semantic search** engine. "I want my money back" finds *"How can I request a refund?"* even though they share no words. You'll compare it with old-school keyword search.

**Like you're 10:** imagine giving every word or sentence a **GPS location** on a giant map of meaning. "Puppy" lives next to "dog", "refund" next to "money back". To find similar things, look at who lives nearby.
**Time:** ~1.5 h · **Builds on:** [5.3 Tiny RNN name generator](../03-tiny-rnn-name-generator) · **Needs:** internet once for Part B (the ~90 MB embedding model); no API key

## Why this matters
Embeddings are how AI systems compare meaning. They're the "R" in **RAG** (Level 7): when a chatbot answers questions about your PDFs, it first embeds your question and finds the paragraphs whose embeddings are closest. The same trick powers "related products", duplicate-question detection, search that understands synonyms, and clustering customer feedback by topic.

## What you'll learn
- **Embedding**: a list of numbers (a vector) that represents meaning. Similar meaning → vectors point the same way.
- **Distributional hypothesis**: words used in similar contexts have similar meanings. Part A *is* this idea in 20 lines.
- **Cosine similarity**: how closely two vectors point in the same direction (1 = same, 0 = unrelated). With unit-length vectors it's just a dot product.
- **Keyword vs semantic search**: TF-IDF matches *words*; sentence embeddings match *meaning*.

## Before you start
```bash
pip install -r requirements.txt
```
- `numpy`: the vectors, SVD and dot products.
- `scikit-learn`: `TfidfVectorizer` for the keyword-search baseline.
- `sentence-transformers`: loads the pretrained `all-MiniLM-L6-v2` sentence-embedding model (it also installs PyTorch and Hugging Face `transformers`, so this install is big, ~1 GB with PyTorch).

No API key needed. The first run of Part B downloads `all-MiniLM-L6-v2` (~90 MB) from huggingface.co and caches it; after that it works offline. Part A needs nothing but numpy.

## Run it
1. From the course root:
   ```bash
   cd level-5-text-models/04-embeddings-find-similar-sentences
   pip install -r requirements.txt
   ```
2. Part A, word vectors from scratch:
   ```bash
   python word_vectors_from_scratch.py
   ```
3. Part B, keyword search vs semantic search on 5 built-in questions:
   ```bash
   python semantic_search.py
   ```
4. Ask your own questions (each in quotes):
   ```bash
   python semantic_search.py "do you ship to germany?"
   ```

### What you should see
Part A (real output):
```
king   -> [('queen', 1.0), ('kingdom', 0.93), ('son', 0.64), ('daughter', 0.64)]
dog    -> [('cat', 0.96), ('mouse', 0.94), ('puppy', 0.77), ('woman', 0.76)]
apple  -> [('banana', 0.96), ('eat', 0.93), ('fruit', 0.55), ('father', 0.34)]
paris  -> [('rome', 0.95), ('berlin', 0.85), ('we', 0.76), ('to', 0.67)]
car    -> [('bus', 1.0), ('bike', 0.9), ('rides', 0.9), ('road', 0.89)]

Nobody told the model that apples and bananas are both fruit. It learned it from which words appear nearby!
```
Part B. The TF-IDF half is real output:
```
===== TF-IDF (keyword matching) =====
  'I want my money back'
     -> How do I reset my password?  (similarity 0.07)
  'I forgot my login'
     -> How do I reset my password?  (similarity 0.09)
  'the box came broken'
     -> Can I change the delivery address after ordering?  (similarity 0.15)
  'stop charging me every month'
     -> How can I request a refund for my order?  (similarity 0.00)
  'is my credit card safe with you'
     -> Is my payment information stored securely?  (similarity 0.18)
```
The embedding half needs the model download, which wasn't possible where this lesson was checked, so this part is an example. You should see every question matched to the right answer, with similarities roughly between 0.3 and 0.7:
```
===== Sentence embeddings (meaning) =====
  'I want my money back'
     -> How can I request a refund for my order?  (similarity 0.52)
  'I forgot my login'
     -> How do I reset my password?  (similarity 0.55)
  'the box came broken'
     -> What should I do if my package arrives damaged?  (similarity 0.48)
  'stop charging me every month'
     -> How do I cancel my subscription?  (similarity 0.41)
  'is my credit card safe with you'
     -> Is my payment information stored securely?  (similarity 0.63)
```
What to look at:
- **Part A:** the model put king/queen, dog/cat, apple/banana, paris/rome together purely from which words appear near which. It's not perfect ("father" near "apple", "we" near "paris"): the corpus is only 38 short sentences.
- **TF-IDF gets 1 of 5 right.** Its similarities are near 0 because the questions share almost no words with the answers. "my" is the only overlap in the first one, so it picks a random-looking answer.
- **Embeddings get all 5**, because they compare meaning, not spelling.

## How it works
### Part A: `word_vectors_from_scratch.py`
1. **`corpus`** is a list of words from 38 short sentences (61 different words) about royalty, pets, fruit, vehicles and cities.
2. **Co-occurrence matrix.** `C[a, b]` counts how often word `b` appears within `window = 2` words of word `a`. "apple" and "banana" both appear near "eat", "a", "sweet", "fruit", so their rows look alike. That's the **distributional hypothesis**: "you shall know a word by the company it keeps".
3. **PPMI** (positive pointwise mutual information) replaces each count with "how much MORE often do these two appear together than chance would predict?" (negative values become 0). Without it, super-common words like "the" and "." would dominate every row.
4. **SVD** (singular value decomposition) compresses the big table (one column per vocabulary word) into 16 numbers per word, keeping the most important patterns. Think of it like describing every word with 16 sliders instead of 61 counts. Each word's 16 numbers are its **embedding**.
5. **Normalising** each vector to length 1 means the dot product of two vectors *is* their **cosine similarity**: 1 = pointing the same way, 0 = unrelated.
6. **`similar(word)`** dot-products one word's vector with all of them and prints the 4 highest (skipping the word itself).

### Part B: `semantic_search.py`
```
FAQ sentences ──embed──► 8 vectors ┐
                                    ├─► dot products (cosine) ─► highest = best answer
your question ──embed──► 1 vector ─┘
```
1. **`FAQ`** is the "knowledge base" (8 support questions). **`queries`** are your command-line questions, or 5 built-in ones that deliberately avoid the FAQ's words.
2. **`embed_with_tfidf`** is the keyword baseline. `TfidfVectorizer` makes one column per word, weighted by **TF-IDF** (term frequency × inverse document frequency: rare words count more than common ones). Each sentence is then scaled to length 1. Two sentences are only similar if they share words.
3. **`embed_with_transformer`** loads `all-MiniLM-L6-v2`, a small transformer (you'll build transformers in Level 6) trained on a billion sentence pairs to put paraphrases close together. `model.encode(..., normalize_embeddings=True)` returns one 384-number unit vector per sentence.
4. **The main loop** runs both methods. For each, it embeds the FAQ once, then for every query computes `faq_vecs @ embed([q])[0]`: the dot product with every FAQ vector = 8 cosine similarities. `argmax` picks the best. If a method can't load (e.g. the model download fails), it prints why and moves on, so you always see the TF-IDF half.

## If something goes wrong
- **`[Sentence embeddings (meaning)] skipped: No module named 'sentence_transformers'`** → run `pip install -r requirements.txt` in your activated virtual environment.
- **`skipped: ... huggingface.co ...` / `Connection error` / `403`** → the model can't be downloaded. Check your internet connection (school and office networks sometimes block huggingface.co); try again on another network. Once downloaded it's cached and works offline.
- **Install fails while building `torch`** → install PyTorch first with the command from https://pytorch.org/get-started/locally/ (choose CPU if you have no NVIDIA GPU), then re-run `pip install -r requirements.txt`.
- **`KeyError: 'xyz'`** in Part A (after you changed the words list) → `similar()` only knows words that appear in `corpus`.
- **The first Part B run is slow** → it's downloading the model and loading PyTorch. Later runs take a few seconds.

## Try this
1. **Your own knowledge base.** Replace `FAQ` with 20 entries about something you know (your school's rules, a game's wiki, your team's onboarding notes) and ask questions in your own words.
   <details><summary>Hint</summary>

   Keep each entry to one clear question or fact, like a real FAQ. Ask with different words from the entries ("when do I need to be in?" vs "School starts at 8:45"). This tiny loop (embed documents once, embed the question, take the most similar) is exactly the retrieval step you'll build in 7.3 RAG, just with a PDF instead of a list.
   </details>
2. **Top 3 and "I don't know".** Show the 3 best matches with scores, and print "no good match" when the best similarity is below 0.4.
   <details><summary>Solution</summary>

   Replace the last two lines of the loop (`best = ...` and the `print`) with:
   ```python
           print(f"  '{q}'")
           if sims.max() < 0.4:
               print("     -> no good match, sorry! (best similarity below 0.4)")
               continue
           for i in sims.argsort()[::-1][:3]:            # the 3 best matches, best first
               print(f"     {sims[i]:.2f}  {FAQ[i]}")
   ```
   Try `python semantic_search.py "how do I reset my password" "what is the weather"`. The weather question has no good answer, and now the program says so instead of guessing. RAG systems use the same kind of threshold to avoid answering from irrelevant documents. (0.4 is a starting point; the right threshold depends on the model and your data.)
   </details>
3. **Draw the map of meaning.** Plot the word vectors from Part A in 2D with matplotlib (`pip install matplotlib`), using the first two of their 16 numbers. Do the groups make sense?
   <details><summary>Solution</summary>

   Add to the end of `word_vectors_from_scratch.py`:
   ```python
   import matplotlib.pyplot as plt
   words = ["king", "queen", "prince", "princess", "dog", "cat", "puppy", "kitten",
            "apple", "banana", "paris", "rome", "berlin", "car", "bus", "bike"]
   plt.figure(figsize=(7, 6))
   for w in words:
       x, y = vectors[idx[w], 0], vectors[idx[w], 1]
       plt.scatter(x, y)
       plt.annotate(w, (x, y))
   plt.title("Word vectors (first 2 of 16 numbers)")
   plt.savefig("word_map.png")
   print("Saved word_map.png")
   ```
   The cities sit together far from the rest, car/bus/bike form their own corner, and pairs like king/queen and puppy/kitten land almost on top of each other. Some groups overlap, because 2 of 16 numbers can't show everything.
   </details>

## Check yourself
1. Why does Part A think "apple" and "banana" are similar, when nobody told it they're fruit?
2. What does a cosine similarity of 1.0 mean? And 0?
3. Why does TF-IDF fail on "I want my money back", and why do embeddings succeed?
4. In a RAG chatbot, what gets embedded, and when?

<details><summary>Answers</summary>

1. They appear next to the same words ("eat", "sweet", "a", "fruit"), so their co-occurrence rows, and therefore their vectors, are similar.
2. 1.0: the vectors point in exactly the same direction (same meaning, as far as the model can tell). 0: they're at right angles, unrelated.
3. TF-IDF only scores shared words, and the question shares none with "How can I request a refund for my order?". The embedding model learned from huge numbers of paraphrases that "money back" and "refund" mean the same thing, so their vectors are close.
4. Every document chunk is embedded once, ahead of time, and stored. Each user question is embedded when it arrives, then compared with the stored vectors to find the most relevant chunks to give the LLM.
</details>

## Learn more (optional)
- Word Embedding and Word2Vec, Clearly Explained (StatQuest): https://www.youtube.com/results?search_query=statquest+word+embedding+and+word2vec+clearly+explained
- Sentence-Transformers documentation: https://www.sbert.net/
- Cosine similarity explained: https://www.youtube.com/results?search_query=cosine+similarity+explained

## Next
→ [5.5 · Sentiment with a pretrained DistilBERT](../05-sentiment-with-pretrained-distilbert)
