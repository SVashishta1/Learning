# A search engine that understands MEANING, built in 20 lines: this is exactly what a vector database does inside.
# Usage: python search.py "I forgot my login"
import sys

import numpy as np
from chromadb.utils.embedding_functions import DefaultEmbeddingFunction

embed = DefaultEmbeddingFunction()

faq = [
    "How do I reset my password?",
    "How can I get a refund for my order?",
    "How long does shipping take?",
    "Can I change my delivery address?",
    "Do you offer student discounts?",
    "How do I cancel my subscription?",
    "Is my payment information safe?",
    "What should I do if my package arrives damaged?",
    "Do you ship internationally?",
    "How do I contact customer support?",
]
faq_vectors = np.array(embed(faq))                 # step 1: turn every FAQ into numbers ONCE

questions = sys.argv[1:] or ["I want my money back", "I forgot my login", "the box came broken", "stop charging me every month"]
for question in questions:
    q = np.array(embed([question])[0])            # step 2: turn the question into numbers
    scores = faq_vectors @ q / (np.linalg.norm(faq_vectors, axis=1) * np.linalg.norm(q))   # step 3: compare with every FAQ
    best = scores.argsort()[::-1][:2]             # step 4: take the 2 closest
    print(f"\n🔎 '{question}'")
    for i in best:
        print(f"   {scores[i]:.2f}  {faq[i]}")
