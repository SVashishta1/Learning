# 07 · Spam or not?

**What it does:** learns from 20 example messages, then tells you whether any new message is spam, and how sure it is.

## Run it
```bash
cd part-2-machine-learning/07-spam-or-not
python spam_detector.py
python spam_detector.py "Congrats! Free cruise, click now" "Dinner at 7?"
```

## The idea in one sentence
The model gives every word a score ("free" and "click" push towards spam, "lunch" pushes towards ok), adds up the scores of a message's words, and turns the total into a percentage.

## Try this
1. Find a message that fools it (e.g. "free lunch tomorrow?"). Why did it get fooled?
2. Add 5 more examples of your own to `messages` and see if it gets smarter.
