# 6.4 · Translator and summariser with Hugging Face

**What you'll build:** an English→French translator and a news summariser using pretrained **encoder-decoder** transformers, a ROUGE score that compares your summary with a human one, and an optional API with `/translate` and `/summarize`.
**Like you're 10:** the **encoder** reads the whole sentence and understands it; the **decoder** writes the answer word by word, glancing back at what the encoder understood. It's like a listener who takes notes and a speaker who reads from them.
**Time:** ~1 h · **Builds on:** [6.3 Fine-tune a small LLM with LoRA](../03-fine-tune-a-small-llm-with-lora) · **Needs:** internet for the first run (downloads ~1.5 GB of models once), ~4 GB free RAM. No GPU, no API key.

## Why this matters
You don't train most models yourself: you download one that someone already trained and use it. The Hugging Face Hub hosts hundreds of thousands of them, and loading one in three lines is a daily task for AI engineers. Translation and summarisation power real features such as "translate this review", "TL;DR this ticket" and meeting notes. You also meet **ROUGE**, the classic way to score generated text, and learn why it isn't enough on its own.

## What you'll learn
- **Encoder-decoder (seq2seq) models**: one half reads the input, the other half writes a new text, which is ideal for "turn text A into text B".
- **Tokenizer + model pair**: every Hub model comes with its own tokenizer, and you must use the matching one.
- **`generate()` and beam search**: how the decoder picks words, keeping several candidate sentences alive at once.
- **Cross-attention**: the decoder attends to the encoder's output (the attention from 6.1, but between two sequences).
- **ROUGE**: a word-overlap score against a reference summary. Fast and objective, but blind to meaning.

## Before you start
```bash
cd level-6-transformers/04-translator-and-summarizer-with-huggingface
pip install -r requirements.txt
```
- `torch`: runs the neural networks.
- `transformers`: downloads and runs pretrained models from the Hugging Face Hub.
- `sentencepiece`, `sacremoses`: the text-splitting tools the MarianMT translator's tokenizer needs.
- `rouge_score`: computes the ROUGE score.
- `fastapi`, `uvicorn[standard]`: only for the optional API.

No API key needed. Models are downloaded on first use and cached (in `~/.cache/huggingface`), so later runs start much faster and work offline.

## Run it
1. From the course root: `cd level-6-transformers/04-translator-and-summarizer-with-huggingface`
2. Run the demo: `python translate_and_summarize.py` (first run: a few minutes of downloading; after that ~10–30 s on a laptop).
3. Optional, the API: `uvicorn api:app --reload`, open http://127.0.0.1:8000/docs, click **POST /translate → Try it out**, type `{"text": "Good morning, my friends."}` and press **Execute**.

### What you should see
```
EN: Machine learning is changing the world.
FR: L'apprentissage automatique change le monde.

EN: Where is the nearest train station?
FR: Où est la gare la plus proche ?

SUMMARY:  The city council voted on Tuesday to turn the old railway line into a 12-kilometre park for walking and cycling. The project, which will cost about 40 million dollars, is expected to take three years.
ROUGE vs a human summary: {'rouge1': 0.576, 'rouge2': 0.281, 'rougeL': 0.475}
```
(Huge downloads can't run in the course's test environment, so this is representative output. Your wording may differ slightly with other library versions, and you will also see download progress bars the first time.)

What to look at:
- The translation is fluent French, not word-by-word. The model learned whole phrases.
- The summary mostly **copies** whole sentences from the article. DistilBART was trained on news, where the first sentences usually carry the main facts, so it learned to keep them.
- **ROUGE-1 ≈ 0.58** means about half the words overlap with the human summary. The summary is good, yet the score is far from 1, because the human used different words ("approved", "$40 million", "12 km"). That's ROUGE's blind spot.

## How it works
```
"Where is the station?" ─► tokenizer ─► [ids] ─► ENCODER (reads everything at once)
                                                     │  understanding of every word
                                                     ▼
                         DECODER writes: "Où" → "est" → "la" → "gare" → ... → </s>
                         (each step: self-attention on what it wrote so far
                          + cross-attention on the encoder's understanding)
```

1. **`load(model_id)`** calls `AutoTokenizer.from_pretrained` and `AutoModelForSeq2SeqLM.from_pretrained`. "Auto" means: read the model's config on the Hub and pick the right class for you (MarianMT for the translator, BART for the summariser). The `Seq2SeqLM` part means "encoder-decoder that generates text".
2. **`translator` and `summarizer`** are loaded once at the top of the file, each as a `(tokenizer, model)` pair. Loading is the slow part, so you never do it inside a loop.
3. **`run(tok, model, text, ...)`** is the whole recipe in three lines: the tokenizer turns text into ids (`truncation=True` cuts anything longer than the model's limit), `model.generate()` runs the encoder once and the decoder step by step until it emits the end token, and `tok.decode()` turns ids back into text.
4. **`translate()`** uses `num_beams=4`. **Beam search** keeps the 4 most likely partial sentences at every step instead of greedily grabbing the single best next word, then returns the best finished sentence. It's slower but gives more natural results.
5. **`summarize()`** adds `max_length`/`min_length` (in tokens) to control the summary size, `no_repeat_ngram_size=3` so it never repeats a 3-word phrase, and `length_penalty=2.0` which nudges beam search towards fuller summaries.
6. **The `__main__` block** translates two sentences, summarises a short news article, then scores the summary with `rouge_scorer.RougeScorer`. ROUGE-1 counts shared single words, ROUGE-2 shared word pairs, ROUGE-L the longest shared sequence. `fmeasure` balances "did I cover the reference?" with "did I add junk?".
7. **`api.py`** imports `translate` and `summarize` (this loads the models once when the server starts) and wraps them in two POST endpoints. `Field(min_length=1, max_length=5000)` rejects empty or giant inputs with a 422 error before they reach the model.

The three transformer families, now that you've used all of them:

| Architecture | Example | Good at |
|--------------|---------|---------|
| Encoder-only | BERT, DistilBERT (5.5) | understanding: classify, extract |
| Decoder-only | GPT (6.2), Llama, Claude | generating: chat, write, code |
| Encoder-decoder | MarianMT, BART, T5 (this project) | turning one text into another: translate, summarise |

## If something goes wrong
- **Very slow first run, or `OSError: We couldn't connect to 'https://huggingface.co'`** → the first run downloads ~1.5 GB. Check your internet connection and wait. After one successful run the models are cached and work offline.
- **`ImportError` mentioning `sentencepiece`, or "Couldn't instantiate the backend tokenizer"** → the translator's tokenizer needs `sentencepiece`. Run `pip install -r requirements.txt` again inside your virtual environment.
- **Process killed / laptop freezes** → you're out of RAM (the summariser alone needs ~2 GB). Close other apps, or try it on Google Colab.
- **`Token indices sequence length is longer than the specified maximum`** → your text is longer than the model's limit (1,024 tokens for DistilBART, 512 for MarianMT). `truncation=True` cuts the rest, so the end of the text is ignored. See *Try this* 2 for the fix.
- **`ERROR: [Errno 98] Address already in use`** when starting the API → another server is on port 8000. Stop it with Ctrl+C or use `uvicorn api:app --reload --port 8001`.

## Try this
1. **Translate into another language.** Change `TRANSLATE_MODEL` to `"Helsinki-NLP/opus-mt-en-de"` (German) or `"Helsinki-NLP/opus-mt-en-hi"` (Hindi) and run again.
   <details><summary>Hint</summary>

   That's the only change needed: each Helsinki-NLP model handles one language pair (`en-de` = English to German). Browse others by searching "opus-mt-en" on huggingface.co/models. If you change the API too, rename the `"french"` key in `api.py`.
   </details>
2. **Summarise a long article.** Paste a long Wikipedia article (more than ~800 words). The end gets cut off. Fix it with "chunk, summarise each chunk, summarise the summaries".
   <details><summary>Solution</summary>

   ```python
   def summarize_long(text, words_per_chunk=500):
       words = text.split()
       chunks = [" ".join(words[i:i + words_per_chunk]) for i in range(0, len(words), words_per_chunk)]
       partial = [summarize(c) for c in chunks]              # one short summary per chunk
       return summarize(" ".join(partial), max_length=120)   # then a summary of the summaries
   ```
   500 words is roughly 650–700 tokens, safely under DistilBART's 1,024 limit. This "map-reduce" idea is also how LLM apps summarise whole books.
   </details>
3. **One model, many tasks.** Load `google/flan-t5-base` with `load()` and give it instructions in the text itself, e.g. `"Translate English to German: How old are you?"` or `"summarize: <article>"` or `"Is this review positive or negative? The food was cold."`.
   <details><summary>Solution</summary>

   ```python
   t5 = load("google/flan-t5-base")
   for prompt in ["Translate English to German: How old are you?",
                  "Is this review positive or negative? The food was cold and the waiter was rude."]:
       print(prompt, "->", run(*t5, prompt, max_new_tokens=40))
   ```
   FLAN-T5 is an encoder-decoder trained on over 1,000 tasks described in plain words, an early step towards the instruction-following LLMs in Level 7.
   </details>

## Check yourself
1. Why is an encoder-decoder a natural fit for translation, while a decoder-only model is a natural fit for chat?
2. What does beam search do better than always picking the single most likely next word?
3. A summary gets ROUGE-1 = 0.2 but a human says it's excellent. How is that possible?
4. Why are the models loaded once at the top of the file and not inside `translate()`?

<details><summary>Answers</summary>

1. Translation has a complete input that should be read in full (both directions) before writing a separate output, which is exactly the encoder + decoder split. Chat is one long text that keeps growing, so "predict the next token of everything so far" (decoder-only) fits.
2. The best first word doesn't always lead to the best sentence. Keeping several candidates lets a slightly less likely start win if it leads to a much better whole sentence.
3. ROUGE only counts shared words. A summary that paraphrases ("approved" instead of "voted for") can be perfect in meaning but share few words with the reference. That's why Level 7 adds LLM-as-judge evaluation.
4. Loading reads hundreds of MB from disk into memory and takes seconds. Doing it once and reusing the model makes every call fast. The API relies on this too.
</details>

## Learn more (optional)
- Hugging Face LLM course: https://huggingface.co/learn/llm-course/chapter1/1
- Encoder-decoder models explained: https://www.youtube.com/results?search_query=encoder+decoder+transformer+explained+translation
- Beam search explained: https://www.youtube.com/results?search_query=beam+search+explained+nlp

## Next
→ [6.5 · Run an open LLM on your laptop](../05-run-an-open-llm-on-your-laptop)
