# Learn to tell spam from normal messages.  Usage: python spam_detector.py "Win a free iPhone now!"
import sys

from sklearn.feature_extraction.text import CountVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline

messages = [
    ("WINNER! Claim your free $1000 gift card now", "spam"), ("Free entry to win cash prizes, text WIN", "spam"),
    ("URGENT: verify your bank password at this link", "spam"), ("Cheap pills, no prescription, order now", "spam"),
    ("You have won a lottery! Send your details to claim", "spam"), ("Click here for a free vacation, limited offer", "spam"),
    ("Earn $500 a day from home, sign up free", "spam"), ("Congratulations, you are selected for a free phone", "spam"),
    ("Your account is suspended, click to restore it now", "spam"), ("Get rich quick with this crypto trick, click", "spam"),
    ("Are we still on for lunch tomorrow?", "ok"), ("Can you send me the notes from class?", "ok"),
    ("I'll be home late, don't wait for dinner", "ok"), ("Happy birthday! Have a great day", "ok"),
    ("The meeting moved to 3pm", "ok"), ("Thanks for helping me with the project", "ok"),
    ("Can you pick up milk on your way home?", "ok"), ("Good luck on your exam tomorrow", "ok"),
    ("Let's watch the match on Saturday", "ok"), ("I sent you the photos from the trip", "ok"),
    ("See you at the cafe at noon", "ok"), ("Lunch was great, see you next week", "ok"),
    ("Can we move our call to tomorrow?", "ok"), ("Dinner at my place tonight?", "ok"),
]
texts = [text for text, label in messages]
labels = [label for text, label in messages]

# A pipeline = 2 steps glued together:
#   CountVectorizer turns each message into word counts (computers need numbers, not words)
#   LogisticRegression learns which words point to spam
model = make_pipeline(CountVectorizer(), LogisticRegression())
model.fit(texts, labels)

# Which words did it learn are the most "spammy"? model[0] is step 1 of the pipeline, model[1] is step 2.
words = model[0].get_feature_names_out()      # every word it saw in the examples
weights = model[1].coef_[0]                   # one score per word: positive = points to spam
top = sorted(zip(weights, words), reverse=True)[:8]
print("Most spammy words:", ", ".join(word for _, word in top))

tests = sys.argv[1:] or ["Claim your free prize now!", "See you at lunch tomorrow", "Click this link to win cash"]
for text in tests:
    # predict_proba gives one chance per label, in the order of model.classes_ (["ok", "spam"]). We want spam's.
    spam_chance = model.predict_proba([text])[0][list(model.classes_).index("spam")]
    print(f"{'🚫 SPAM' if spam_chance > 0.5 else '✅ ok  '} ({spam_chance:.0%})  {text}")
