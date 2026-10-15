"""Project 6.4: translation and summarisation with encoder-decoder transformers, plus scoring with ROUGE.

python translate_and_summarize.py
"""
from rouge_score import rouge_scorer
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

TRANSLATE_MODEL = "Helsinki-NLP/opus-mt-en-fr"         # MarianMT, trained only for English -> French (~300 MB)
SUMMARY_MODEL = "sshleifer/distilbart-cnn-12-6"        # DistilBART fine-tuned on news articles (~1.2 GB)


def load(model_id):
    """Download (first time only, then cached) a tokenizer + encoder-decoder ("seq2seq") model."""
    return AutoTokenizer.from_pretrained(model_id), AutoModelForSeq2SeqLM.from_pretrained(model_id)


def run(tok, model, text, **generate_options):
    """text -> token ids -> ENCODER reads them all -> DECODER writes new tokens one by one -> text."""
    inputs = tok(text, return_tensors="pt", truncation=True)   # truncation: cut inputs longer than the model's limit
    output_ids = model.generate(**inputs, **generate_options)
    return tok.decode(output_ids[0], skip_special_tokens=True)


translator = load(TRANSLATE_MODEL)
summarizer = load(SUMMARY_MODEL)


def translate(text):
    # num_beams=4: "beam search" keeps the 4 best partial sentences at each step, then picks the best finished one
    return run(*translator, text, num_beams=4, max_new_tokens=200)


def summarize(text, max_length=60, min_length=20):
    # no_repeat_ngram_size=3 stops the summary repeating the same 3-word phrase; length_penalty>1 favours longer beams
    return run(*summarizer, text, num_beams=4, max_length=max_length, min_length=min_length,
               no_repeat_ngram_size=3, length_penalty=2.0, do_sample=False)


if __name__ == "__main__":
    # ---- 1. Translation ----
    for s in ["Machine learning is changing the world.", "Where is the nearest train station?"]:
        print(f"EN: {s}\nFR: {translate(s)}\n")

    # ---- 2. Summarisation ----
    article = """The city council voted on Tuesday to turn the old railway line into a 12-kilometre park for walking
and cycling. The project, which will cost about 40 million dollars, is expected to take three years. Supporters
say the park will reduce traffic, improve air quality and give families a safe place to exercise. Some local
business owners worried about construction noise, but the council promised to limit work to daytime hours.
The first section, near the central station, should open next summer."""
    summary = summarize(article)
    print("SUMMARY:", summary)

    # ---- 3. Score it: ROUGE compares word overlap with a human-written reference summary (0 = none, 1 = identical) ----
    reference = ("The council approved a $40 million plan to turn an old railway into a 12 km walking "
                 "and cycling park within three years.")
    scorer = rouge_scorer.RougeScorer(["rouge1", "rouge2", "rougeL"], use_stemmer=True)
    scores = scorer.score(reference, summary)                  # score(target, prediction)
    print("ROUGE vs a human summary:", {name: round(s.fmeasure, 3) for name, s in scores.items()})
