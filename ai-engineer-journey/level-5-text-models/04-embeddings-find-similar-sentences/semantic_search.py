"""Project 5.4 part B: semantic search with a pretrained sentence-embedding model.
Finds the FAQ answer that MEANS the same as your question, even with zero shared words.

python semantic_search.py "how do I get my money back?"
"""
import sys

import numpy as np

FAQ = [
    "How can I request a refund for my order?",
    "What are your shipping times to Europe?",
    "How do I reset my password?",
    "Can I change the delivery address after ordering?",
    "Do you offer student discounts?",
    "How do I cancel my subscription?",
    "Is my payment information stored securely?",
    "What should I do if my package arrives damaged?",
]
queries = sys.argv[1:] or ["I want my money back", "I forgot my login", "the box came broken",
                           "stop charging me every month", "is my credit card safe with you"]


def embed_with_transformer(texts):                       # (texts unused: the model is already trained)
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer("all-MiniLM-L6-v2")      # ~90 MB download the first time; 384-number vectors
    return lambda batch: model.encode(batch, normalize_embeddings=True)


def embed_with_tfidf(texts):
    from sklearn.feature_extraction.text import TfidfVectorizer
    vec = TfidfVectorizer().fit(texts + queries)           # one column per word, weighted by how rare it is

    def embed(batch):
        m = vec.transform(batch).toarray()
        return m / (np.linalg.norm(m, axis=1, keepdims=True) + 1e-9)   # unit length, so dot product = cosine
    return embed


for name, make in [("TF-IDF (keyword matching)", embed_with_tfidf), ("Sentence embeddings (meaning)", embed_with_transformer)]:
    try:
        embed = make(FAQ)
    except Exception as e:
        print(f"\n[{name}] skipped: {e}\n  -> run: pip install sentence-transformers"
              "\n  -> the model downloads from huggingface.co the first time, so you need internet once")
        continue
    faq_vecs = embed(FAQ)
    print(f"\n===== {name} =====")
    for q in queries:
        sims = faq_vecs @ embed([q])[0]                  # cosine similarity with every FAQ entry
        best = int(sims.argmax())
        print(f"  '{q}'\n     -> {FAQ[best]}  (similarity {sims[best]:.2f})")
