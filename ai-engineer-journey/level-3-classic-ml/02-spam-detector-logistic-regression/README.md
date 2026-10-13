# 3.2 · Spam detector: logistic regression

**What you build:** a filter that reads a message and says spam or ham (not spam), shows its confidence, and tells you *which words* made it decide.
**Like you're 10:** every word carries a little weight. "FREE", "claim" and "winner" push toward the SPAM side of a seesaw; "lunch", "tomorrow" and "thanks" push toward HAM. Add up the pushes and see which way it tips.

## Run it
```bash
cd level-3-classic-ml/02-spam-detector-logistic-regression
pip install -r requirements.txt
python spam_detector.py                              # small built-in dataset (70 messages)
python spam_detector.py --full                       # real UCI dataset (5,574 SMS) if you're online
python spam_detector.py "Congrats! You won a free car, click now"
```

## Key ideas
- **Bag of words:** turn text into numbers by counting words. `ngram_range=(1, 2)` also counts word *pairs* like "click here".
- **Logistic regression** = linear regression squeezed through a sigmoid (from 2.2!) so the output is a probability between 0 and 1.
- **Precision vs recall** (read the report):
  - *Precision (spam):* of the messages flagged as spam, how many really were? Low precision means real messages go to the junk folder. Users hate that.
  - *Recall (spam):* of all real spam, how much did we catch?
- **Pipeline:** vectoriser + model saved as ONE object, so the exact same text processing happens in training and in production.

## Your turn
1. Swap `CountVectorizer` for `TfidfVectorizer`. Does the report change?
2. Only flag spam when `p_spam > 0.8`. What happens to precision and recall? (You're trading one for the other.)
3. Write 5 tricky messages (e.g. "free lunch tomorrow?") that fool your model, and explain why.

## Watch
- Logistic Regression (StatQuest): https://www.youtube.com/results?search_query=statquest+logistic+regression
- Sensitivity/specificity and precision/recall (StatQuest): https://www.youtube.com/results?search_query=statquest+precision+recall
