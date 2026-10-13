# 5.4 · Embeddings: find similar words and sentences

**What you build:**
- **Part A:** word vectors from scratch (co-occurrence counts + SVD). The model discovers that "apple" is like "banana" and "paris" is like "rome", without being told.
- **Part B:** a **semantic search** engine. "I want my money back" finds *"How can I request a refund?"* even though they share no words. You'll compare it with old-school keyword search.

**Like you're 10:** imagine giving every word or sentence a **GPS location** on a giant map of meaning. "Puppy" lives next to "dog", "refund" next to "money back". To find similar things, look at who lives nearby.

**Why this matters:** this exact technique is the "R" in **RAG** (Level 7). It's how chatbots find the right paragraph in your PDFs.

## Run it
```bash
cd level-5-text-models/04-embeddings-find-similar-sentences
pip install -r requirements.txt
python word_vectors_from_scratch.py
python semantic_search.py
python semantic_search.py "do you ship to germany?"
```

## Key ideas
- **Embedding** = a list of numbers (a vector) that represents meaning. Similar meaning → vectors point the same way.
- **Cosine similarity** = how closely two vectors point in the same direction (1 = same, 0 = unrelated). With unit-length vectors it's just a dot product.
- **Distributional hypothesis:** words used in similar contexts have similar meanings. Part A *is* this idea in 20 lines.
- **TF-IDF vs. embeddings:** TF-IDF matches *words*; embeddings match *meaning*. Part B shows where keyword search fails.
- `all-MiniLM-L6-v2` is a small transformer trained to put paraphrases close together. It's fast and great for search.

## Your turn
1. Add 20 of your own FAQ entries (school rules, a game's wiki...) and ask questions.
2. Show the top 3 matches with scores, and add a "no good match" message when the best similarity is below 0.4.
3. Plot the word vectors from part A in 2D (use the first two columns) with matplotlib. Do the clusters make sense?

## Watch
- Word Embedding and Word2Vec, Clearly Explained (StatQuest): https://www.youtube.com/results?search_query=statquest+word+embedding+and+word2vec+clearly+explained
- Sentence-Transformers docs: https://www.sbert.net/
