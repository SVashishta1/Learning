"""Project 5.1: (A) count words, (B) build a Naive Bayes sentiment classifier from scratch. Pure Python.

python sentiment.py                      # train + test
python sentiment.py "what a great film"  # try your own sentence
"""
import math
import re
import sys
from collections import Counter

from reviews import REVIEWS, TEST

STOPWORDS = set("a an the and or but i it is was to of in on for my me so this that by too from at be".split())


def tokenize(text: str) -> list[str]:
    words = re.findall(r"[a-z']+", text.lower())          # lowercase, keep only letters
    return [w for w in words if w not in STOPWORDS]        # drop words that carry no feeling


# ---- A. Word counting ----
all_words = Counter(w for _, text in REVIEWS for w in tokenize(text))
print("Most common words:", all_words.most_common(8))
pos_words = Counter(w for label, text in REVIEWS if label == 1 for w in tokenize(text))
neg_words = Counter(w for label, text in REVIEWS if label == 0 for w in tokenize(text))
print("Top positive words:", [w for w, _ in pos_words.most_common(6)])
print("Top negative words:", [w for w, _ in neg_words.most_common(6)])


# ---- B. Naive Bayes: "how likely is each word in positive vs negative reviews?" ----
class NaiveBayes:
    def fit(self, data):
        self.counts = {0: Counter(), 1: Counter()}
        self.docs = Counter(label for label, _ in data)
        for label, text in data:
            self.counts[label].update(tokenize(text))
        self.vocab = set(self.counts[0]) | set(self.counts[1])
        return self

    def log_prob(self, text, label):
        total = sum(self.counts[label].values())
        score = math.log(self.docs[label] / sum(self.docs.values()))           # prior: how common is this class?
        for w in tokenize(text):
            # +1 "Laplace smoothing": an unseen word shouldn't make the probability exactly zero
            score += math.log((self.counts[label][w] + 1) / (total + len(self.vocab)))
        return score

    def predict(self, text):
        lp, ln = self.log_prob(text, 1), self.log_prob(text, 0)
        p_pos = 1 / (1 + math.exp(ln - lp))                                    # turn the two scores into a probability
        return int(p_pos > 0.5), p_pos


model = NaiveBayes().fit(REVIEWS)
correct = 0
print("\nTest reviews:")
for label, text in TEST:
    pred, p = model.predict(text)
    correct += pred == label
    print(f"  {'✅' if pred == label else '❌'} {p:5.0%} positive | {text}")
print(f"Accuracy: {correct}/{len(TEST)}")

for text in sys.argv[1:]:
    pred, p = model.predict(text)
    print(f"\n'{text}' -> {'POSITIVE' if pred else 'NEGATIVE'} ({p:.0%})")

print("\nWeakness of bag of words, word order is ignored:")
for text in ["not good, actually bad", "not bad, actually good"]:
    print(f"  '{text}' -> {model.predict(text)[1]:.0%} positive (same words = same score!)")
