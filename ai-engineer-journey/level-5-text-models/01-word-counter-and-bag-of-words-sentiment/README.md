# 5.1 · Word counter + bag-of-words sentiment

**What you'll build:** (A) a word counter that finds the most "positive" and "negative" words in movie reviews, and (B) a **Naive Bayes** sentiment classifier written from scratch in pure Python, with no libraries at all.
**Like you're 10:** sort reviews into a happy pile and a grumpy pile. Count how often each word appears in each pile. For a new review, ask "do its words show up more in the happy pile or the grumpy pile?"
**Time:** ~1 h · **Builds on:** [3.2 Spam detector](../../level-3-classic-ml/02-spam-detector-logistic-regression) and [4.5 Draw-a-digit web app](../../level-4-computer-vision/05-draw-a-digit-web-app) · **Needs:** nothing extra (just Python)

## Why this matters
Computers can't read; they can only do maths on numbers. Every text model, from a spam filter to ChatGPT, starts by turning text into numbers. Counting words is the oldest way to do it, and Naive Bayes on word counts is still used for quick, cheap text classification (spam, topic tagging, support-ticket routing). Building it by hand shows you exactly what "a model learning from text" means, and exactly where it breaks.

## What you'll learn
- **Tokenisation**: splitting text into pieces (here: lowercase words). 5.6 builds the smarter version GPT uses.
- **Stopwords**: very common words ("the", "and", "a") that carry no feeling, so we drop them.
- **Naive Bayes**: scoring a text by how likely its words are in each class, assuming each word is independent ("naive").
- **Log probabilities and Laplace smoothing**: two tricks that keep the maths from breaking.
- **The limit of bag of words**: word order is thrown away, so "not good" and "good, not" look the same.

## Before you start
No packages to install: this lesson is pure Python (the 3.11+ from Level 0 is perfect). `requirements.txt` is empty on purpose.

No API key or internet needed. The reviews are in `reviews.py`: 30 training reviews (15 positive, 15 negative) and 6 test reviews.

## Run it
1. From the course root:
   ```bash
   cd level-5-text-models/01-word-counter-and-bag-of-words-sentiment
   ```
2. Train and test:
   ```bash
   python sentiment.py
   ```
3. Classify your own sentences (each one in quotes):
   ```bash
   python sentiment.py "the acting was brilliant" "what a boring mess"
   ```

### What you should see
```
Most common words: [('acting', 3), ('loved', 3), ('funny', 3), ('great', 3), ('were', 3), ('plot', 3), ('characters', 3), ('brilliant', 2)]
Top positive words: ['loved', 'great', 'brilliant', 'funny', 'exciting', 'clever']
Top negative words: ['boring', 'fell', 'terrible', 'acting', 'plot', 'awful']

Test reviews:
  ✅   94% positive | Wonderful and funny, a brilliant family film
  ✅   88% positive | Great acting and an exciting story
  ✅    7% positive | Awful script and boring characters
  ✅    7% positive | Slow, dull and a waste of my evening
  ✅   94% positive | I loved the beautiful music and the clever plot
  ✅    5% positive | Bad jokes and terrible pacing
Accuracy: 6/6

'the acting was brilliant' -> POSITIVE (66%)

'what a boring mess' -> NEGATIVE (14%)

Weakness of bag of words, word order is ignored:
  'not good, actually bad' -> 14% positive (same words = same score!)
  'not bad, actually good' -> 14% positive (same words = same score!)
```
What to look at:
- **The word lists**: the classifier has no idea what "loved" means; it just noticed "loved" appears in happy reviews.
- **"acting" and "plot" are in the negative list**: they're neutral words that happen to appear in more negative reviews. With 30 reviews, coincidences like this are common.
- **The last two lines**: opposite meanings, identical score. That's the big limitation.

## How it works
1. **`tokenize(text)`** lowercases the text and uses a regular expression, `[a-z']+`, to grab runs of letters (and apostrophes, so "don't" stays one word). Then it removes `STOPWORDS`. `"The acting was brilliant!"` → `['acting', 'brilliant']`.
2. **Part A: counting.** `Counter` (from Python's `collections`) counts things. `all_words` counts every token in every review; `pos_words` and `neg_words` count only in positive or negative reviews. `.most_common(6)` gives the top 6.
3. **Part B: `NaiveBayes.fit(data)`** is the training. It just counts:
   - `self.docs`: how many reviews of each class (15 and 15);
   - `self.counts[label]`: how often each word appears in that class's reviews;
   - `self.vocab`: every word seen in training.
4. **`log_prob(text, label)`** scores "how likely is this text if it were a `label` review?":
   - start with the **prior**: the share of reviews in that class (here 15/30 = 0.5);
   - for each word, multiply by P(word | class) = (times the word appeared in that class + 1) / (total words in that class + vocabulary size).
   - The **+1 is Laplace smoothing**. Without it, a word never seen in positive reviews would have probability 0, and multiplying by 0 wipes out the whole score, whatever the other words say.
   - Multiplying many small probabilities gives numbers so tiny the computer rounds them to 0 (**underflow**). So we add their **logarithms** instead: log(a × b) = log(a) + log(b). Same ranking, safe numbers.
5. **`predict(text)`** computes the log score for both classes and turns the difference into a probability with `1 / (1 + exp(ln - lp))`. That's the sigmoid from Level 2 again. Above 50% → positive.
6. **The test loop** prints ✅ or ❌ for each test review, then the accuracy. Then your command-line sentences are scored, and finally the "not good / not bad" demo shows that word order is invisible to this model. Fixing that is why we need sequence models (5.3) and transformers (5.5 and Level 6).

It's called **naive** because it assumes every word is independent of the others ("brilliant" and "acting" don't affect each other). That's obviously false, yet it works surprisingly well for sorting text.

## If something goes wrong
- **`ModuleNotFoundError: No module named 'reviews'`** → run the script from inside the project folder (step 1), where `reviews.py` lives.
- **`TypeError: 'type' object is not subscriptable`** at `list[str]` → your Python is older than 3.9. Install Python 3.11+ (see Level 0).
- **The ✅/❌ symbols show as `?` or cause `UnicodeEncodeError`** (older Windows terminals) → use Windows Terminal, or run `set PYTHONIOENCODING=utf-8` first.
- **Your sentence gets ~50%** → none of its words were in the training reviews (unknown words are smoothed and cancel out). Use words like the ones in `reviews.py`, or add more reviews.

## Try this
1. **Break it with sarcasm.** Add 10 reviews of your own to `REVIEWS` in `reviews.py` (format: `(1, "text")` for positive, `(0, "text")` for negative), and test some sarcastic sentences. Where does it fail?
   <details><summary>Hint</summary>

   Try `python sentiment.py "Oh great, another two hours of my life I will never get back"`: the original model says POSITIVE (78%) because of "great". `"I loved how boring it was"` → 56% positive. Sarcasm flips meaning without changing the words, and word counting only sees words.
   </details>
2. **Count word pairs.** Make `tokenize` also return **bigrams** (pairs of neighbouring words like `not_good`). Does the "not good / not bad" example improve?
   <details><summary>Solution</summary>

   Replace the last line of `tokenize` with:
   ```python
       words = [w for w in words if w not in STOPWORDS]
       return words + [a + "_" + b for a, b in zip(words, words[1:])]   # add word pairs like "not_good"
   ```
   Surprise: both still get the same score (13%). The pairs `not_good` and `not_bad` never appear in the training reviews, so the model has learned nothing about them. Now add two training reviews, `(0, "Not good at all, the story was a mess")` and `(1, "Not bad at all, actually a lovely film")`, and run again: 16% vs 44%. New features only help when the training data contains examples of them.
   </details>
3. **The library version.** Do the same with scikit-learn (`pip install scikit-learn`) in a few lines, and compare.
   <details><summary>Solution</summary>

   Save as `sklearn_version.py` in this folder:
   ```python
   from sklearn.feature_extraction.text import CountVectorizer
   from sklearn.naive_bayes import MultinomialNB
   from sklearn.pipeline import make_pipeline
   from reviews import REVIEWS, TEST

   model = make_pipeline(CountVectorizer(stop_words="english"), MultinomialNB())
   model.fit([t for _, t in REVIEWS], [label for label, _ in REVIEWS])
   print("accuracy:", model.score([t for _, t in TEST], [label for label, _ in TEST]))
   print(model.predict_proba(["not good, actually bad", "not bad, actually good"])[:, 1])
   ```
   Accuracy 1.0, and the two "not" sentences again get identical scores (0.25 each). `MultinomialNB` uses the same +1 smoothing by default (`alpha=1.0`): it's the same algorithm you wrote.
   </details>

## Check yourself
1. What would happen without the +1 (Laplace smoothing) if a test review contained a word never seen in positive reviews?
2. Why do we add logarithms instead of multiplying probabilities?
3. Why do "not good, actually bad" and "not bad, actually good" get exactly the same score?
4. "acting" ended up in the top negative words. Is acting a negative word? What does this tell you about small datasets?

<details><summary>Answers</summary>

1. That word's probability would be 0, so the whole positive score would become 0 (or log(0) = minus infinity), no matter how positive the other words were.
2. Multiplying dozens of tiny numbers underflows to 0 in floating point. Adding their logs gives the same comparison with numbers of a sensible size.
3. After tokenising, both are the same bag of words {not, good, actually, bad}. Bag of words ignores order, so the model literally sees the same input.
4. No, it's neutral. It just appeared in more negative reviews by chance. With little data, models learn coincidences; more and more varied data fixes this.
</details>

## Learn more (optional)
- Naive Bayes, Clearly Explained (StatQuest): https://www.youtube.com/results?search_query=statquest+naive+bayes+clearly+explained
- Python `collections.Counter`: https://docs.python.org/3/library/collections.html#collections.Counter
- Speech and Language Processing, chapter "Naive Bayes and Sentiment Classification" (free book by Jurafsky & Martin): https://web.stanford.edu/~jurafsky/slp3/

## Next
→ [5.2 · Next-letter predictor: a bigram name generator](../02-next-letter-predictor-bigram-name-generator)
