# Level 5 · Small text models: teaching a computer to read

Text is harder than images because words have *meaning*, *order* and *context*. This level climbs the same ladder researchers climbed: counting words → predicting the next letter → networks with memory → embeddings that capture meaning → pretrained transformers. It ends with a BPE tokenizer, the exact first step of GPT.

| # | Project | Idea | Time |
|---|---------|------|------|
| 5.1 | [Word counter + bag-of-words sentiment](01-word-counter-and-bag-of-words-sentiment) | text → numbers; Naive Bayes from scratch | 1 h |
| 5.2 | [Next-letter predictor (bigram)](02-next-letter-predictor-bigram-name-generator) | language modelling = predicting what comes next | 1.5 h |
| 5.3 | [Tiny RNN name generator](03-tiny-rnn-name-generator) | networks with memory | 2 h |
| 5.4 | [Embeddings: find similar sentences](04-embeddings-find-similar-sentences) | meaning as vectors; semantic search (the heart of RAG!) | 1.5 h |
| 5.5 | [Sentiment with pretrained DistilBERT](05-sentiment-with-pretrained-distilbert) | Hugging Face, fine-tuning a transformer | 2 h |
| 5.6 | [BPE tokenizer from scratch](06-bpe-tokenizer-from-scratch) | how GPT chops text into tokens | 2 h |

```bash
pip install numpy torch scikit-learn sentence-transformers transformers datasets tiktoken
```
That covers the whole level, but you don't need it all at once: 5.1 and 5.6 are pure Python, 5.2 needs only `numpy`, 5.3 only `torch`. Each project folder has its own `requirements.txt` (`pip install -r requirements.txt` inside a folder). No API keys. No GPU needed; 5.5's fine-tuning is the only slow part on a CPU (~20 minutes), and it runs in about a minute on Google Colab's free GPU.

**Downloads:** 5.2 fetches a 230 KB list of names; 5.4 and 5.5 download pretrained models and data from huggingface.co the first time (~90 MB for 5.4, ~600 MB for 5.5), then work offline.

**Watch:** Karpathy's *makemore* series goes perfectly with 5.2 and 5.3: https://www.youtube.com/watch?v=PaCmpygFfXo

**Finish line for Level 5:** your RNN beats the bigram's loss (5.3), semantic search finds answers that share no words with the question (5.4), and your own BPE tokenizer round-trips text with emoji (5.6). Then go to [Level 6 · Transformers](../level-6-transformers).
