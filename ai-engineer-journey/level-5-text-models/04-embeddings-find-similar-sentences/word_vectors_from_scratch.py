"""Project 5.4 part A: word vectors from scratch. 'You shall know a word by the company it keeps.'
Count which words appear near which, then compress those counts with SVD into short vectors."""
import numpy as np

corpus = """the king rules the kingdom with the queen . the queen rules the kingdom with the king .
the prince is the son of the king . the princess is the daughter of the queen .
a man walks the dog . a woman walks the dog . the man is a father . the woman is a mother .
the dog chases the cat . the cat chases the mouse . the puppy is a young dog . the kitten is a young cat .
i eat an apple . i eat a banana . an apple is a fruit . a banana is a fruit . i drink milk . i drink juice .
the car drives on the road . the bus drives on the road . a bike rides on the road .
paris is a city in france . rome is a city in italy . berlin is a city in germany .
i visited paris last summer . i visited rome last summer . i visited berlin last summer .
we flew to paris . we flew to rome . we flew to berlin . the train to rome is fast . the train to paris is fast .
the dog barks . the puppy barks . the cat meows . the kitten meows . i eat a sweet apple . i eat a sweet banana .""".split()

vocab = sorted(set(corpus))
idx = {w: i for i, w in enumerate(vocab)}
window = 2

# 1. Co-occurrence matrix: C[a, b] = how often word b appears within 2 words of word a
C = np.zeros((len(vocab), len(vocab)))
for i, w in enumerate(corpus):
    for j in range(max(0, i - window), min(len(corpus), i + window + 1)):
        if i != j:
            C[idx[w], idx[corpus[j]]] += 1

# 2. PPMI: "does b appear near a MORE than chance would predict?" This stops "the" and "." from dominating.
total = C.sum()
with np.errstate(divide="ignore"):
    C = np.maximum(np.log(C * total / (C.sum(1, keepdims=True) * C.sum(0, keepdims=True))), 0)

# 3. Compress with SVD: keep the 16 most important "directions" -> each word becomes 16 numbers
U, S, _ = np.linalg.svd(C)
vectors = U[:, :16] * S[:16]
vectors /= np.linalg.norm(vectors, axis=1, keepdims=True)   # unit length, so dot product = cosine similarity


def similar(word, k=4):
    sims = vectors @ vectors[idx[word]]
    sims[idx[word]] = -1                                  # don't return the word itself
    return [(vocab[i], round(float(sims[i]), 2)) for i in sims.argsort()[::-1][:k]]


for w in ["king", "dog", "apple", "paris", "car"]:
    print(f"{w:6s} -> {similar(w)}")
print("\nNobody told the model that apples and bananas are both fruit. It learned it from which words appear nearby!")
