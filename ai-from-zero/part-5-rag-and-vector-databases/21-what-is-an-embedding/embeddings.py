# Turn text into lists of numbers ("embeddings") and see that similar MEANING gives similar numbers.
import numpy as np
from chromadb.utils.embedding_functions import DefaultEmbeddingFunction

embed = DefaultEmbeddingFunction()        # a small free model that runs on your computer

vector = embed(["I love pizza"])[0]
print(f"'I love pizza' became {len(vector)} numbers. The first 6: {np.round(vector[:6], 3)}\n")


def similarity(a, b):
    """1.0 = same meaning, around 0 = unrelated. (This is called 'cosine similarity'.)"""
    va, vb = embed([a, b])
    return float(np.dot(va, vb) / (np.linalg.norm(va) * np.linalg.norm(vb)))


pairs = [
    ("I love pizza", "Pizza is my favourite food"),
    ("I love pizza", "I enjoy eating Italian food"),
    ("How do I get a refund?", "I want my money back"),
    ("The cat sat on the mat", "A kitten was resting on the rug"),
    ("I love pizza", "The stock market fell today"),
    ("How do I get a refund?", "What's the weather tomorrow?"),
]
for a, b in pairs:
    score = similarity(a, b)
    print(f"{score:.2f} {'█' * int(score * 30):30s} '{a}'  vs  '{b}'")
