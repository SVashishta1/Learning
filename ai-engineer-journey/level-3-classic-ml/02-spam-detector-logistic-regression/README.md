# 3.2 · Spam detector: logistic regression

**What you'll build:** a filter that reads a text message and says **spam** or **ham** (not spam), shows how confident it is, and tells you *which words* made it decide.
**Like you're 10:** every word carries a little weight. "FREE", "claim" and "winner" push toward the SPAM side of a seesaw; "lunch", "tomorrow" and "thanks" push toward HAM. Add up the pushes and see which way it tips.
**Time:** ~1 h · **Builds on:** [3.1 House price predictor](../01-house-price-predictor-linear-regression) · **Needs:** nothing extra (internet only for the optional `--full` dataset)

## Why this matters
Turning text into numbers and putting a simple classifier on top is still how many real filters work: spam folders, "is this support ticket urgent?", content moderation, routing emails to the right team. It trains in a second, runs on any laptop, and you can see exactly which words drive each decision. It's also the baseline you must beat before paying for a big language model.

## What you'll learn
- **Classification**: predicting a category (spam / ham) instead of a number.
- **Bag of words**: turning a message into numbers by counting its words, ignoring their order.
- **Logistic regression**: linear regression squeezed through a sigmoid so the output is a probability between 0 and 1.
- **Precision vs recall**: two different ways a filter can fail, and why you usually trade one for the other.
- **Pipeline**: gluing the text-to-numbers step and the model into one object so they always work together.

## Before you start
```bash
pip install -r requirements.txt
```
- `pandas`: reads `messages.csv` into a table.
- `scikit-learn`: the bag-of-words vectoriser, logistic regression and the evaluation report.

No API key needed. The small dataset (`messages.csv`, 70 messages: 35 spam, 35 ham) is in the folder. `--full` downloads the real UCI SMS Spam Collection (5,574 messages, ~200 KB) if you're online.

## Run it
1. From the course root:
   ```bash
   cd level-3-classic-ml/02-spam-detector-logistic-regression
   pip install -r requirements.txt
   ```
2. Train and evaluate on the small built-in dataset:
   ```bash
   python spam_detector.py
   ```
3. Classify your own message (put it in quotes):
   ```bash
   python spam_detector.py "Congrats! You won a free car, click now"
   ```
4. Train on the real 5,574-message dataset (needs internet; falls back to `messages.csv` if the download fails):
   ```bash
   python spam_detector.py --full
   ```

### What you should see
```
              precision    recall  f1-score   support

         ham      0.909     1.000     0.952        10
        spam      1.000     0.909     0.952        11

    accuracy                          0.952        21
   macro avg      0.955     0.955     0.952        21
weighted avg      0.957     0.952     0.952        21

Confusion matrix (rows = truth, cols = prediction) [ham, spam]:
[[10  0]
 [ 1 10]]

Most SPAMMY words: now, your, free, claim, cash, link, click, and, in, needed, prize, won
Most HAMMY words:  the, you, for, on, at, let, is, me, tomorrow, do, are you, can

'Claim your free prize now' -> SPAM (98% spam)

'Can we meet for coffee tomorrow?' -> ham (8% spam)
```
What to look at:
- **The test set is 21 messages** (30% of 70). The model got 20 right.
- **The confusion matrix**: top row = real ham (10 correct, 0 wrongly flagged). Bottom row = real spam (1 slipped through, 10 caught).
- **Spam precision 1.000**: every message it flagged really was spam, so no friend's message went to junk. **Spam recall 0.909**: it caught 10 of 11 spam messages.
- **The word lists** are the model's "reasoning". With only 70 messages it also learns odd words like "and" and "in". With `--full` the lists look much more sensible.

## How it works
```
"Claim your free prize now"
        │  CountVectorizer: count each word and word pair
        ▼
[claim:1, your:1, free:1, prize:1, now:1, "claim your":1, ...]   (thousands of columns, mostly 0)
        │  LogisticRegression: add up weight × count, squeeze through a sigmoid
        ▼
P(spam) = 0.98  ──►  0.98 > THRESHOLD (0.5)  ──►  SPAM
```
1. **`load(full)`** returns a table with a `label` column (`spam`/`ham`) and a `text` column. With `--full` it downloads the UCI zip, opens the `SMSSpamCollection` file inside it and splits each line at the tab. If anything fails, it prints why and reads `messages.csv` instead (`SMALL_DATA` points to the file next to the script, so it works from any folder).
2. **`train_test_split(..., test_size=0.3, stratify=df.label)`** keeps 30% of messages for testing. `stratify` makes sure the test set has the same spam/ham mix as the whole dataset.
3. **`CountVectorizer`** is the **bag of words**. It builds a vocabulary from the training messages, then turns each message into a row of counts, one column per word. Word order is thrown away, like tipping the words into a bag. `ngram_range=(1, 2)` also counts **word pairs** ("click here", "claim your"), which keeps a little bit of order. `lowercase=True` makes "FREE" and "free" the same word.
4. **`LogisticRegression`** learns one weight per column. It adds up `weight × count` for the message (exactly like linear regression in 3.1), then squeezes the total through a **sigmoid** (from 2.2) so it lands between 0 and 1. That number is the probability of spam. `C=5` controls how strongly weights are kept small (bigger `C` = less restraint). `max_iter=1000` gives the solver enough steps to finish.
5. **`make_pipeline(...)`** glues both steps into one `model`. `model.fit(...)` fits the vectoriser *and* the classifier; `model.predict_proba(...)` runs a raw message through both. This means the exact same text processing happens in training and when you use it later.
6. **`predict_proba(X_test)[:, 1]`** gives P(spam) for each test message (scikit-learn sorts class names alphabetically, so column 0 is "ham" and column 1 is "spam"). Anything above **`THRESHOLD`** is called spam.
7. **`classification_report`** prints:
   - **Precision (spam)**: of the messages flagged as spam, how many really were? Low precision = real messages go to the junk folder. Users hate that.
   - **Recall (spam)**: of all real spam, how much did we catch?
   - **F1**: one number that balances the two. **Support**: how many test messages are in that class.
8. **The word lists.** `model[0]` is the vectoriser and `model[-1]` the classifier. `clf.coef_[0]` holds the weight of every word. Sorting them shows the 12 most positive (spammy) and 12 most negative (hammy) words.
9. **Your messages.** Any text you pass on the command line is scored; otherwise two examples are.

## If something goes wrong
- **`FileNotFoundError: messages.csv`** → the CSV must stay in the same folder as `spam_detector.py`. Re-download the folder if you moved or deleted it.
- **`(couldn't download the full dataset: ...)`** with `--full` → you're offline, behind a firewall, or the UCI site is down. The script continues with the small dataset; try again later.
- **Your message is classified strangely** → with 70 training messages the model has seen very few words. Words it has never seen are ignored completely. Try `--full` for a much bigger vocabulary.
- **`ModuleNotFoundError: No module named 'sklearn'`** → activate your virtual environment and run `pip install -r requirements.txt`.

## Try this
1. **Swap the vectoriser.** Replace `CountVectorizer` with `TfidfVectorizer` (in the import line and in `make_pipeline`). TF-IDF gives less weight to words that appear in almost every message. Does the report change?
   <details><summary>Hint</summary>

   Import line: `from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer`. On the small dataset accuracy goes from 0.952 to 0.905 (one more spam slips through), but the spammy word list loses "and" and "in" and gains "win" and "claim your". Small datasets are noisy; compare on `--full` too.
   </details>
2. **Be more careful.** Set `THRESHOLD = 0.8` so you only flag spam when the model is very sure. What happens to precision and recall?
   <details><summary>Hint</summary>

   Spam precision stays 1.000 but recall drops from 0.909 to 0.455: only 5 of 11 spam messages are caught. A higher threshold means fewer false alarms but more missed spam. Try `0.2` too: recall goes back up, but precision falls to 0.769 because some real messages get flagged.
   </details>
3. **Fool your model.** Write 5 tricky messages that it gets wrong, e.g. a real message full of "spammy" words, or spam written in a friendly tone. Explain each mistake by looking at the word lists.
   <details><summary>Hint</summary>

   Try `python spam_detector.py "free lunch tomorrow?"` (43% spam: "free" pushes up, "tomorrow" pulls down). Spam that avoids the trigger words ("Hey, saw your profile, let's chat at this site", 42%) passes, while a friend writing "I won! Call me now" (65%) or "Your prize from the school raffle is ready, claim it now" (73%) gets flagged. Bag of words only sees *which* words appear, not what they mean together.
   </details>

## Check yourself
1. What does "bag of words" throw away, and why can that cause mistakes?
2. A spam filter has high recall but low precision. What do users experience?
3. Why do we put the vectoriser and the model in one pipeline instead of using them separately?
4. The model says a message is 55% spam. What decides whether it is called spam?

<details><summary>Answers</summary>

1. Word order (and therefore meaning that depends on order). "Not free" and "free, not" look identical; "free lunch tomorrow" scores spammy just because of "free".
2. Almost all spam is caught, but lots of real messages are wrongly sent to the junk folder.
3. So the exact same text processing (vocabulary, lowercasing, word pairs) is used in training and in production. Using them separately makes it easy to forget a step or use a different vocabulary later.
4. The threshold. With `THRESHOLD = 0.5` it's spam; with `0.8` it's ham. Choosing the threshold is a business decision about which mistake is worse.
</details>

## Learn more (optional)
- Logistic Regression (StatQuest): https://www.youtube.com/results?search_query=statquest+logistic+regression
- Sensitivity/specificity and precision/recall (StatQuest): https://www.youtube.com/results?search_query=statquest+precision+recall
- scikit-learn text feature extraction: https://scikit-learn.org/stable/modules/feature_extraction.html#text-feature-extraction

## Next
→ [3.3 · Iris flower classifier: a decision tree](../03-iris-flower-classifier-decision-tree)
