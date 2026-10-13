"""Project 5.5 part A: use a model someone already fine-tuned for sentiment, in 3 lines."""
from transformers import pipeline

clf = pipeline("sentiment-analysis", model="distilbert-base-uncased-finetuned-sst-2-english")   # ~250 MB once

tests = [
    "This movie was absolutely wonderful!",
    "not good, actually bad",
    "not bad, actually good",               # the case that fooled bag-of-words in 5.1!
    "I expected to hate it, but it won me over.",
    "The food was cold and the waiter ignored us.",
]
for text, result in zip(tests, clf(tests)):
    print(f"{result['label']:8s} {result['score']:.1%}  | {text}")
