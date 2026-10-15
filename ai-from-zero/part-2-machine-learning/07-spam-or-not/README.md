# 07 · Spam or not?

**What you'll build:** a spam filter that learns from 24 example messages, then tells you whether any new message is spam, and how sure it is.
**Time:** ~30 min · **Builds on:** [06 · Predict house prices](../06-predict-house-prices) · **Needs:** nothing extra

Like you're 10: after seeing enough junk mail, you notice that "FREE!!!" and "click now" usually mean junk. The computer learns the same hints, one word at a time.

## Why this matters
Sorting things into groups is called **classification**, and it's one of the most common jobs for machine learning: spam filters, fraud alerts, "is this review positive or negative?", sorting support tickets. It's also your first taste of turning **text** into numbers a computer can learn from. Every AI that reads language, including Claude, starts by turning words into numbers, just in a much smarter way.

## What you'll learn
- **Classification**: predicting a category (spam / ok) instead of a number.
- **Bag of words**: turning a message into counts of each word, so the computer has numbers to work with.
- **Logistic regression**: a model that gives every word a score, adds up the scores of a message's words, and turns the total into a probability between 0% and 100%.
- **Pipeline**: two or more steps glued together, so text goes in one end and a prediction comes out the other.
- **Probability and threshold**: the model says "83% spam"; you decide that anything over 50% counts as spam.

## Before you start
- Venv on, and this part's install line done (skip if done in lesson 06):
  ```bash
  pip install scikit-learn joblib fastapi "uvicorn[standard]"
  ```
  This lesson uses `scikit-learn` only.
- No API key needed.

## Run it
1. From the course folder (`ai-from-zero`):
   ```bash
   cd part-2-machine-learning/07-spam-or-not
   python spam_detector.py
   ```
2. Test your own messages. Put each one in quotes:
   ```bash
   python spam_detector.py "Congrats! Free cruise, click now" "Dinner at 7?"
   ```

### What you should see
```
Most spammy words: free, click, now, this, your, claim, win, selected
🚫 SPAM (83%)  Claim your free prize now!
✅ ok   (15%)  See you at lunch tomorrow
🚫 SPAM (78%)  Click this link to win cash
```
and for your own messages:
```
Most spammy words: free, click, now, this, your, claim, win, selected
🚫 SPAM (80%)  Congrats! Free cruise, click now
✅ ok   (26%)  Dinner at 7?
```
The first line shows the words the model learned are the strongest signs of spam. The percentage is the model's chance that the message is spam. Over 50% gets the 🚫 label. Notice "this" and "your" made the list: they appeared in several spam examples, so the model trusts them, even though they're normal words. With only 24 examples, it learns some silly hints too.

## How it works
```
"Claim your free prize now!"
      │  CountVectorizer
      ▼
{claim: 1, your: 1, free: 1, prize: 1, now: 1}      (word counts)
      │  LogisticRegression: add up each word's score
      ▼
total score ──▶ squeezed into 0–100% ──▶ 83% spam ──▶ over 50%? ──▶ 🚫 SPAM
```
1. `messages` is a list of `(text, label)` pairs: 10 spam and 14 ok. The two list comprehensions split it into `texts` (the inputs) and `labels` (the answers).
2. `make_pipeline(CountVectorizer(), LogisticRegression())` builds a two-step model:
   - `CountVectorizer` makes a vocabulary of every word in the examples, then turns each message into counts of those words. It lowercases everything and ignores punctuation. Words it never saw during training are simply ignored later.
   - `LogisticRegression` learns one **weight** (score) per word: positive pushes towards spam, negative towards ok.
3. `model.fit(texts, labels)` runs both steps on the examples: build the vocabulary, count, learn the weights.
4. **The spammy words.** `model[0]` is the first step (the vectorizer) and `model[1]` the second (the classifier). `get_feature_names_out()` lists the vocabulary; `coef_[0]` holds the weight of each word in the same order. `sorted(zip(weights, words), reverse=True)[:8]` pairs them up, sorts biggest first, and keeps the top 8.
5. **Testing messages.** `tests = sys.argv[1:] or [...]` uses the messages you typed, or three examples if you typed none.
6. `model.predict_proba([text])[0]` gives two probabilities, one per label, in the order of `model.classes_`, which is `["ok", "spam"]` (alphabetical). `list(model.classes_).index("spam")` finds spam's position, so `spam_chance` is the spam probability.
7. The `print` uses `spam_chance > 0.5` to choose the label, and `:.0%` to show 0.83 as `83%`.

## If something goes wrong
- **`ModuleNotFoundError: No module named 'sklearn'`** → switch your venv on and run the pip line.
- **Your message got split into several results** → you forgot the quotes. `python spam_detector.py Hi there` tests "Hi" and "there" separately; `python spam_detector.py "Hi there"` tests one message.
- **On Mac/Linux, a message with `!` gives `event not found`** → some terminals treat `!` specially inside double quotes. Use single quotes instead: `python spam_detector.py 'Win now!'`.
- **A message that is obviously spam is marked ok (or the other way round)** → that's not a bug: the model only learned from 24 messages. It can only judge words it has seen. See **Try this**.
- **`ValueError` after you added examples** → check every new line in `messages` is `("text", "spam")` or `("text", "ok")` with a comma after the closing bracket.

## Try this
1. Find messages that fool it. Try `"Claim your seat at lunch now"`, `"Your free trial is over"` and `"Act fast, exclusive deal ends tonight"`. Why did it get each one wrong?
2. Add 5 more examples of your own to `messages` (some spam, some ok) and test the same messages again. Does it get smarter?
3. Print the 8 most "ok" words too (the words with the most negative weights).

<details><summary>Hints and solutions</summary>

1. You get:
   ```
   🚫 SPAM (57%)  Claim your seat at lunch now
   🚫 SPAM (71%)  Your free trial is over
   ✅ ok   (33%)  Act fast, exclusive deal ends tonight
   ```
   The first two are normal messages that use "spammy" words (claim, your, now, free). The third is spam made of words the model has never seen, so they count for nothing. It only knows words, not meaning.
2. For example, add these lines inside `messages` (before the closing `]`):
   ```python
   ("Act now, exclusive deal ends tonight", "spam"), ("Limited offer: claim your reward", "spam"),
   ("Reply YES to win a cash prize", "spam"), ("Free trial of the gym this week, want to come?", "ok"),
   ("Can you claim our seats at lunch?", "ok"),
   ```
   Then "Act fast, exclusive deal ends tonight" becomes 🚫 SPAM (66%). The other two are still marked spam (63% and 70%), but less sure: a few examples help, and real filters learn from millions.
3. Sort without `reverse=True`, so the most negative weights come first. Add after the "Most spammy words" print:
   ```python
   safe = sorted(zip(weights, words))[:8]
   print("Most ok words:", ", ".join(word for _, word in safe))
   ```
   You get `Most ok words: the, on, tomorrow, can, great, dinner, we, lunch`.
</details>

## Check yourself
1. Why does the message need to go through `CountVectorizer` before `LogisticRegression`?
2. What does a big positive weight on the word "free" mean?
3. The model says a message is 52% spam. What does that tell you, compared with 99%?
4. Why does "Act fast, exclusive deal ends tonight" fool the original model?

<details><summary>Answers</summary>

1. Models work with numbers, not text. The vectorizer turns each message into word counts the model can do maths with.
2. Messages containing "free" were usually spam in the examples, so "free" pushes a message's score strongly towards spam.
3. At 52% the model is barely leaning towards spam; it's close to a coin flip. At 99% it is very confident. Both get the same label, so the percentage tells you more than the label.
4. None of its words appeared in the training examples, so they have no weight. The model has nothing to go on and falls back to "ok".
</details>

## Learn more (optional)
- scikit-learn: working with text data: https://scikit-learn.org/stable/tutorial/text_analytics/working_with_text_data.html
- Google's Machine Learning Crash Course, "Logistic regression" and "Classification": https://developers.google.com/machine-learning/crash-course
- Video: search YouTube for "StatQuest logistic regression".

## Next
→ [08 · Flower guesser](../08-flower-guesser)
