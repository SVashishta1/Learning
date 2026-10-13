# 5.1 · Word counter + bag-of-words sentiment

**What you build:** (A) a word counter that finds the most "positive" and "negative" words in movie reviews, and (B) a **Naive Bayes** sentiment classifier written from scratch in pure Python.
**Like you're 10:** sort reviews into a happy pile and a grumpy pile. Count how often each word appears in each pile. For a new review, ask "do its words show up more in the happy pile or the grumpy pile?"

## Run it
```bash
cd level-5-text-models/01-word-counter-and-bag-of-words-sentiment
python sentiment.py
python sentiment.py "the acting was brilliant" "what a boring mess"
```

## Key ideas
- **Tokenization:** splitting text into words (the version in 5.6 is much smarter).
- **Stopwords:** "the", "and", "a" appear everywhere and tell you nothing.
- **Naive Bayes:** multiply per-word probabilities (as a sum of logs, so the numbers don't underflow). It's "naive" because it assumes words are independent.
- **Laplace smoothing (+1):** stops one unseen word from zeroing everything out.
- **The big limitation** is shown at the end: "not good, actually bad" and "not bad, actually good" get *identical* scores because order is ignored. Fixing that is why we need sequence models (5.3) and transformers (Level 6).

## Your turn
1. Add 10 reviews of your own, including tricky sarcastic ones. Where does it fail?
2. Count **bigrams** (word pairs like "not good") as extra features. Does the "not good/not bad" example improve?
3. Compare with scikit-learn: `CountVectorizer` + `MultinomialNB` in 5 lines.

## Watch
- Naive Bayes, Clearly Explained (StatQuest): https://www.youtube.com/results?search_query=statquest+naive+bayes+clearly+explained
