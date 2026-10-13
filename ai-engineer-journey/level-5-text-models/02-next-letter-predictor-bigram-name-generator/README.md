# 5.2 · Next-letter predictor: a bigram name generator

**What you build:** a model that reads 32,000 real names, learns which letter tends to follow which, and **invents new names**. It's the simplest possible *language model*, and the ancestor of GPT.
**Like you're 10:** after "q" almost always comes "u". After "." (the start), names often begin with "a", "k" or "m". Write those odds down for every pair of letters, then roll dice letter by letter.

## Run it
```bash
cd level-5-text-models/02-next-letter-predictor-bigram-name-generator
pip install -r requirements.txt
python bigram.py      # downloads names.txt (~230 KB) the first time
```
You'll get names like "lia", "kanen" or "brayla". Some are lovely, some are nonsense, because the model only remembers ONE previous letter.

## Key ideas
- **Language model** = a probability for the next token given the previous ones. ChatGPT does exactly this, with ~100k-token vocabularies and thousands of tokens of context.
- **Counting is training:** for bigrams the "best" model is just the normalised counts.
- **Sampling:** pick the next letter randomly *according to* its probability. That's why chatbots give different answers each time.
- **Negative log-likelihood loss:** how surprised the model is by real data. The same loss trains GPT (cross-entropy).

## Your turn
1. Make a **trigram** model (two letters of context). Is the loss lower? Do the names look better?
2. Train on a different list: Pokémon, city names, or song titles.
3. Recreate the counts as a one-layer neural net in PyTorch (Karpathy does this in the video) and check you get the same loss.

## Watch (do this one, it's perfect for this project)
- The spelled-out intro to language modeling: building makemore (Karpathy): https://www.youtube.com/watch?v=PaCmpygFfXo
