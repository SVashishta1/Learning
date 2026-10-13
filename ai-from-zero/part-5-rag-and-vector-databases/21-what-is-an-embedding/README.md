# 21 · What is an embedding?

**What it does:** turns sentences into lists of 384 numbers and shows that sentences with similar **meaning** get similar numbers, even when they share no words ("refund" vs "money back").

## Run it
```bash
cd part-5-rag-and-vector-databases/21-what-is-an-embedding
python embeddings.py
```

## The idea in one sentence
An **embedding** is like GPS coordinates for meaning: texts that mean similar things end up close together, so a computer can measure "how similar" with simple maths.

## Try this
1. Add your own pairs, including the same sentence in two languages ("I love dogs" / "J'adore les chiens").
2. Find two sentences with *similar words* but *different meanings* ("The bank of the river" vs "The bank approved my loan"). What score do they get?
