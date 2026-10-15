# 5.5 · Sentiment with a pretrained DistilBERT

**What you'll build:**
- **Part A:** sentiment analysis with a ready-made Hugging Face model, in 3 lines. It handles "not bad, actually good" correctly, which bag-of-words (5.1) couldn't.
- **Part B:** **fine-tune** a plain DistilBERT on 2,000 IMDB movie reviews yourself, with a plain PyTorch loop, and watch accuracy jump from a coin flip (~50%) to ~85–90%.

**Like you're 10:** DistilBERT has already read a huge pile of books and Wikipedia, so it understands English. Fine-tuning is like teaching that well-read friend one new job ("tell me if a review is happy or sad") with a short practice session.
**Time:** ~2 h · **Builds on:** [5.4 Embeddings](../04-embeddings-find-similar-sentences) and [5.1 bag of words](../01-word-counter-and-bag-of-words-sentiment) · **Needs:** internet once (~250 MB of models, ~80 MB of IMDB data); a GPU is optional (Google Colab has free ones)

## Why this matters
This is how most text classification is done at work today: start from a pretrained transformer, either use a model someone already fine-tuned, or fine-tune one on a few thousand of your own examples. It powers review analysis, support-ticket triage, content moderation and intent detection in chatbots. The Hugging Face Hub, tokenizers, attention masks and the fine-tuning loop you use here are the same tools you'll use for LLMs in Level 6.

## What you'll learn
- **Pretrained transformer**: DistilBERT (66M parameters) learned English by filling in masked-out words in books and Wikipedia.
- **Hugging Face `pipeline`**: download and run a ready-made model in one line.
- **Tokenizer + attention mask**: text becomes sub-word token ids, padded to equal length, with a mask saying which tokens are real.
- **Fine-tuning**: add a new 2-class "head" and train the *whole* model briefly with a tiny learning rate (3e-5).
- **Before/after evaluation**: measuring on held-out reviews proves the fine-tuning worked.

## Before you start
```bash
pip install -r requirements.txt
```
- `torch`: runs the model and the training loop.
- `transformers`: Hugging Face's library of pretrained models, tokenizers and `pipeline`.
- `datasets`: Hugging Face's library for downloading and processing datasets (IMDB).

No API key needed. Downloads, once each, cached in `~/.cache/huggingface`:
- Part A: `distilbert-base-uncased-finetuned-sst-2-english` (~270 MB).
- Part B: `distilbert-base-uncased` (~270 MB) and the IMDB dataset (~80 MB).

**No GPU?** Part B takes ~15–25 minutes on a laptop CPU, ~1 minute on a GPU. For the fast version, open https://colab.research.google.com, choose *Runtime → Change runtime type → T4 GPU*, run `!pip install transformers datasets` in a cell, then paste all of `fine_tune.py` into the next cell and run it (Colab ignores `--smoke`, so it does the real run).

## Run it
1. From the course root:
   ```bash
   cd level-5-text-models/05-sentiment-with-pretrained-distilbert
   pip install -r requirements.txt
   ```
2. Part A, a ready-made sentiment model:
   ```bash
   python use_pretrained.py
   ```
3. Part B, wiring check (64 reviews, short texts, about a minute including downloads):
   ```bash
   python fine_tune.py --smoke
   ```
4. Part B for real (2,000 reviews, 1 epoch; saves `my-sentiment-model/`):
   ```bash
   python fine_tune.py
   ```

### What you should see
huggingface.co couldn't be reached where this lesson was checked, so the outputs below are examples of what a real run prints. The code itself was run end to end with a tiny stand-in model and stand-in reviews.

Part A:
```
POSITIVE 99.9%  | This movie was absolutely wonderful!
NEGATIVE 99.9%  | not good, actually bad
POSITIVE 99.8%  | not bad, actually good
POSITIVE 99.7%  | I expected to hate it, but it won me over.
NEGATIVE 99.9%  | The food was cold and the waiter ignored us.
```
Part B (real run; loss values jump around from batch to batch):
```
Example tokens: ['token', '##izer', '##s', 'split', 'un', '##bel', '##ie', '##va', '##bly', 'long', 'words', '.']
Accuracy BEFORE fine-tuning: 50.2% (coin flip)
step   0 | loss 0.697
step  20 | loss 0.612
step  40 | loss 0.401
step  60 | loss 0.288
step  80 | loss 0.352
step 100 | loss 0.205
step 120 | loss 0.263
Accuracy AFTER fine-tuning:  87.6%
Saved to ./my-sentiment-model  ->  pipeline('sentiment-analysis', model='my-sentiment-model')
```
What to look at:
- **Part A gets "not good, actually bad" and "not bad, actually good" right**, the pair that got identical scores in 5.1. A transformer reads words *in context*, so word order matters.
- **The tokens**: common words stay whole; rare words like "unbelievably" are split into known pieces (`##` means "continues the previous piece"). You'll build a tokenizer like this in 5.6.
- **Before ≈ 50%, after ≈ 85–90%** after a single pass over 2,000 reviews. The new head starts random; the pretrained body already understands English, so a little practice goes a long way.
- You'll also see a warning like *"Some weights of DistilBertForSequenceClassification were not initialized ... pre_classifier, classifier"*. That's expected: it's the new head, and training it is exactly what Part B does.

## How it works
### Part A: `use_pretrained.py`
`pipeline("sentiment-analysis", model="distilbert-base-uncased-finetuned-sst-2-english")` downloads a DistilBERT that someone already fine-tuned on SST-2 (a dataset of movie-review sentences), plus its matching tokenizer. Calling `clf(tests)` tokenises each sentence, runs the model, applies softmax and returns `{"label": "POSITIVE", "score": 0.999}` per sentence. Three lines, because someone else did the training. Always check the Hub first: your problem may already be solved.

### Part B: `fine_tune.py`
```
review text ─► tokenizer ─► input_ids + attention_mask ─► DistilBERT body (pretrained) ─► new head (random) ─► 2 scores
                                                                     └──────────── all weights fine-tuned, lr 3e-5 ───────┘
```
1. **Settings.** `--smoke` shrinks everything (64 train / 32 test reviews, 64 tokens each) for a quick check; otherwise 2,000 / 500 reviews, up to 256 tokens each. `device` picks GPU if available.
2. **Data.** `load_dataset("stanfordnlp/imdb")` downloads 50,000 movie reviews labelled 0 = negative, 1 = positive. `.shuffle(seed=0).select(range(N))` takes a random but repeatable slice, because IMDB is sorted by label and the first 2,000 would all be negative.
3. **Tokenizer.** `AutoTokenizer.from_pretrained("distilbert-base-uncased")` loads the exact tokenizer DistilBERT was trained with (it must match the model, like a key and its lock). `encode` turns each review into:
   - `input_ids`: token numbers, cut at `MAX_LEN` (`truncation=True`) and padded with `[PAD]` up to `MAX_LEN` (`padding="max_length"`) so a batch is a neat rectangle;
   - `attention_mask`: 1 for real tokens, 0 for padding, so the model ignores the padding.
   `.map(encode, batched=True)` applies it to every review, and `.with_format("torch", ...)` makes the dataset hand out PyTorch tensors.
4. **Model.** `AutoModelForSequenceClassification.from_pretrained(..., num_labels=2, id2label=labels, ...)` loads the pretrained DistilBERT body and adds a *new*, randomly initialised classification head with 2 outputs. That's why accuracy starts at a coin flip.
5. **Optimizer.** `AdamW` with `lr=3e-5`, about 30× smaller than in 4.1. The body's weights already encode a lot of knowledge; big steps would wreck it ("catastrophic forgetting"). Fine-tuning = small nudges.
6. **`accuracy()`** runs the test reviews in batches of 32 under `model.eval()` + `torch.no_grad()`, takes `argmax` of the 2 scores (`.logits`) and compares with the labels.
7. **Training loop.** One pass over the 2,000 reviews in shuffled batches of 16 (125 steps). Passing `labels=` makes the model compute the cross-entropy loss itself (`out.loss`), then the usual `backward()` → `step()` → `zero_grad()`. Every 20 steps it prints the batch loss.
8. **Save.** `save_pretrained("my-sentiment-model")` writes the weights and config; `tok.save_pretrained` writes the tokenizer next to them. Now `pipeline("sentiment-analysis", model="my-sentiment-model")` loads *your* model exactly like Part A loaded someone else's. The `labels` dictionary given to `from_pretrained` is saved too, so it answers `NEGATIVE`/`POSITIVE` instead of `LABEL_0`/`LABEL_1`.

## If something goes wrong
- **`OSError: We couldn't connect to 'https://huggingface.co'`** → the first run needs internet to download the models and data. Some school/office networks block huggingface.co; try another network. After one successful download everything is cached.
- **Part B is very slow on CPU** → expected (~15–25 min). Use `--smoke` to check the wiring, then use Google Colab's free GPU for the real run (see "Before you start"), or lower the sizes on the `N_TRAIN, N_TEST, MAX_LEN` line (e.g. `(1000, 200, 128)`): faster, slightly less accurate.
- **`RuntimeError: CUDA out of memory` / `MPS backend out of memory`** → lower the training `batch_size=16` to 8, or `MAX_LEN` to 128.
- **`ModuleNotFoundError: No module named 'datasets'`** → activate your virtual environment and run `pip install -r requirements.txt`.
- **Warning "Some weights ... were not initialized"** → normal for Part B (it's the new head). Only worry if you see it in Part A.

## Try this
1. **Emotions instead of sentiment.** Find a model on https://huggingface.co/models for emotions (joy, anger, fear...) and use it with `pipeline`.
   <details><summary>Solution</summary>

   Search the Hub for "emotion" and filter by the *Text Classification* task. A popular one is `j-hartmann/emotion-english-distilroberta-base`:
   ```python
   from transformers import pipeline
   clf = pipeline("text-classification", model="j-hartmann/emotion-english-distilroberta-base", top_k=None)
   for scores in clf(["I can't believe I won!", "Why would you do that to me?", "There's a noise downstairs..."]):
       best = max(scores, key=lambda s: s["score"])
       print(best["label"], f"{best['score']:.0%}")
   ```
   `top_k=None` returns a score for every emotion, not just the best one. Read the model card: it tells you which labels exist and what data it was trained on.
   </details>
2. **Your own data.** Fine-tune on your own labelled examples from a CSV file.
   <details><summary>Hint</summary>

   Make `my_train.csv` and `my_test.csv` with a header row `text,label` and one example per row (label 0 or 1; quote texts that contain commas). In `fine_tune.py` replace the three data lines with:
   ```python
   data = load_dataset("csv", data_files={"train": "my_train.csv", "test": "my_test.csv"})
   train = data["train"].shuffle(seed=0)
   test = data["test"]
   ```
   Aim for at least a few hundred examples per class. For more than 2 classes, set `num_labels` to your number of classes and use labels 0, 1, 2…
   </details>
3. **Sarcasm showdown.** Does 5.1's Naive Bayes or this model handle sarcasm better? Write 5 sarcastic reviews and test both.
   <details><summary>Hint</summary>

   Put your sentences in the `tests` list of `use_pretrained.py`, and run the same ones with `python ../01-word-counter-and-bag-of-words-sentiment/sentiment.py "..."` (from inside the 5.1 folder). Try "Oh great, another two hours of my life I will never get back" (5.1 said 78% positive). The transformer gets more right because it reads context, but sarcasm still fools it sometimes: it has to infer meaning that isn't in the words.
   </details>

## Check yourself
1. Why does accuracy start at about 50% in Part B, even though DistilBERT is pretrained?
2. Why is the learning rate so small (3e-5) compared with 4.1 (1e-3)?
3. What is the attention mask for?
4. When would you use Part A's approach, and when Part B's?

<details><summary>Answers</summary>

1. The classification head (the last layer that turns DistilBERT's understanding into "positive/negative") is brand new and random. The body understands English, but nobody has told it what to output yet.
2. The pretrained weights already contain valuable knowledge. Small steps adjust them to the new task without destroying what they learned (catastrophic forgetting).
3. Reviews have different lengths, so short ones are padded to fill the batch. The mask (1 = real token, 0 = padding) tells the model to ignore the padding.
4. Part A when a model for your exact task already exists and is good enough: no training needed. Part B when your task, labels or kind of text are specific (your product's reviews, your support categories) and you have some labelled examples.
</details>

## Learn more (optional)
- Hugging Face LLM course, chapters 1–3 (free): https://huggingface.co/learn/llm-course/chapter1/1
- BERT explained: https://www.youtube.com/results?search_query=BERT+explained+transformer+encoder+simply
- Hugging Face `pipeline` documentation: https://huggingface.co/docs/transformers/main_classes/pipelines

## Next
→ [5.6 · BPE tokenizer from scratch](../06-bpe-tokenizer-from-scratch)
