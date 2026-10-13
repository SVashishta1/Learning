# Level 5 · Small text models: teaching a computer to read

Text is harder than images because words have *meaning*, *order* and *context*. This level climbs the same ladder researchers climbed: counting words → predicting the next letter → networks with memory → embeddings that capture meaning → pretrained transformers. Ending with a BPE tokenizer gives you the exact input stage of GPT.

| # | Project | Idea |
|---|---------|------|
| 5.1 | [Word counter + bag-of-words sentiment](01-word-counter-and-bag-of-words-sentiment) | text → numbers; Naive Bayes from scratch |
| 5.2 | [Next-letter predictor (bigram)](02-next-letter-predictor-bigram-name-generator) | language modelling = predicting what comes next |
| 5.3 | [Tiny RNN name generator](03-tiny-rnn-name-generator) | networks with memory |
| 5.4 | [Embeddings: find similar sentences](04-embeddings-find-similar-sentences) | meaning as vectors; semantic search (the heart of RAG!) |
| 5.5 | [Sentiment with pretrained DistilBERT](05-sentiment-with-pretrained-distilbert) | Hugging Face, fine-tuning a transformer |
| 5.6 | [BPE tokenizer from scratch](06-bpe-tokenizer-from-scratch) | how GPT chops text into tokens |

**Watch:** Karpathy's makemore series (5.2, 5.3): https://www.youtube.com/watch?v=PaCmpygFfXo
