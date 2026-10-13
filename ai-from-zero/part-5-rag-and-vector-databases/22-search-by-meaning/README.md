# 22 · Search by meaning

**What it does:** a mini search engine for a help-centre FAQ. "I want my money back" finds *"How can I get a refund?"* even though no words match.

## Run it
```bash
cd part-5-rag-and-vector-databases/22-search-by-meaning
python search.py
python search.py "can you deliver to Japan?"
```

## The idea in one sentence
Turn every document into numbers once, turn the question into numbers, and return the documents whose numbers are closest. That's **vector search**, the "R" (retrieval) in RAG.

## Try this
1. Add 5 FAQs about your school, job or hobby, and search them.
2. Show only results with a score above 0.5, and print "No good match" otherwise.
