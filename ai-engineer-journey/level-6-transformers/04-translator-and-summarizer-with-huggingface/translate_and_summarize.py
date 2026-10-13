"""Project 6.4: translation and summarisation with encoder-decoder transformers, plus scoring with ROUGE.

python translate_and_summarize.py
"""
from transformers import pipeline

# ---- 1. Translation: a model trained only for English -> French (~300 MB) ----
translator = pipeline("translation", model="Helsinki-NLP/opus-mt-en-fr")
for s in ["Machine learning is changing the world.", "Where is the nearest train station?"]:
    print(f"EN: {s}\nFR: {translator(s)[0]['translation_text']}\n")

# ---- 2. Summarisation: DistilBART fine-tuned on news articles (~1.2 GB) ----
summarizer = pipeline("summarization", model="sshleifer/distilbart-cnn-12-6")
article = """The city council voted on Tuesday to turn the old railway line into a 12-kilometre park for walking
and cycling. The project, which will cost about 40 million dollars, is expected to take three years. Supporters
say the park will reduce traffic, improve air quality and give families a safe place to exercise. Some local
business owners worried about construction noise, but the council promised to limit work to daytime hours.
The first section, near the central station, should open next summer."""
summary = summarizer(article, max_length=60, min_length=20, do_sample=False)[0]["summary_text"]
print("SUMMARY:", summary)

# ---- 3. Score it: ROUGE compares overlap with a human-written reference summary ----
try:
    import evaluate
    rouge = evaluate.load("rouge")
    reference = "The council approved a $40 million plan to turn an old railway into a 12 km walking and cycling park within three years."
    print("ROUGE vs a human summary:", {k: round(v, 3) for k, v in rouge.compute(predictions=[summary], references=[reference]).items()})
except Exception as e:
    print("(pip install evaluate rouge_score to compute ROUGE)", e)
