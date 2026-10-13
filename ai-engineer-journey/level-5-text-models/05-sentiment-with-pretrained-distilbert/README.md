# 5.5 · Sentiment with a pretrained DistilBERT

**What you build:**
- **Part A:** sentiment analysis with a ready-made Hugging Face model, in 3 lines. It handles "not bad, actually good" correctly, which bag-of-words (5.1) couldn't.
- **Part B:** **fine-tune** a plain DistilBERT on 2,000 IMDB reviews yourself and watch accuracy jump from ~50% to ~88%.

**Like you're 10:** DistilBERT has already read a huge chunk of the internet, so it understands English. Fine-tuning is like teaching that well-read friend one new job ("tell me if a review is happy or sad") with a short practice session.

## Run it
```bash
cd level-5-text-models/05-sentiment-with-pretrained-distilbert
pip install -r requirements.txt
python use_pretrained.py          # part A (downloads ~250 MB once)
python fine_tune.py --smoke       # part B wiring check
python fine_tune.py               # part B for real (CPU: ~20 min; Google Colab GPU: ~1 min)
```
**No GPU?** Open https://colab.research.google.com, choose *Runtime → Change runtime type → T4 GPU*, then run `!pip install transformers datasets` and paste in `fine_tune.py`.

## Key ideas
- **Pretrained transformer:** DistilBERT (66M parameters) learned language by predicting masked words in books and Wikipedia.
- **Fine-tuning:** add a small classification head and train *everything* briefly with a **tiny learning rate** (3e-5).
- **Tokenizer:** splits text into sub-word pieces ("unbelievably" → "un", "##bel", "##ie", "##va", "##bly"). It must match the model.
- **Attention mask:** tells the model which tokens are real and which are padding.
- **Hugging Face Hub:** thousands of ready models. Always check whether someone has already solved your problem!

## Your turn
1. Find a model on https://huggingface.co/models for emotions (joy/anger/fear...) and use it with `pipeline`.
2. Fine-tune on your own data: put `text,label` rows in a CSV and use `load_dataset("csv", data_files=...)`.
3. Compare: does 5.1's Naive Bayes or this model handle sarcasm better? Write 5 sarcastic reviews.

## Watch
- Hugging Face course, chapter 1-3 (free): https://huggingface.co/learn/llm-course/chapter1/1
- BERT explained: https://www.youtube.com/results?search_query=BERT+explained+transformer+encoder+simply
