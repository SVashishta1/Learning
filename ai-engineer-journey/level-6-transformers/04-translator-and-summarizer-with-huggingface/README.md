# 6.4 · Translator and summariser with Hugging Face

**What you build:** an English→French translator and a news summariser using pretrained **encoder-decoder** transformers, a ROUGE score against a human summary, and an optional API with `/translate` and `/summarize`.
**Like you're 10:** the **encoder** reads the whole sentence and understands it; the **decoder** writes the answer word by word, glancing back at what the encoder understood. It's like a listener who takes notes and a speaker who reads from them.

## Run it
```bash
cd level-6-transformers/04-translator-and-summarizer-with-huggingface
pip install -r requirements.txt
python translate_and_summarize.py       # downloads ~1.5 GB of models the first time
uvicorn api:app --reload                # optional: try it at http://127.0.0.1:8000/docs
```

## Key ideas
| Architecture | Example | Good at |
|--------------|---------|---------|
| Encoder-only | BERT, DistilBERT (5.5) | understanding: classify, extract |
| Decoder-only | GPT (6.2), Llama, Claude | generating: chat, write, code |
| Encoder-decoder | MarianMT, BART, T5 (this project) | turning one text into another: translate, summarise |

- **`pipeline()`** = tokenizer + model + post-processing in one call.
- **Cross-attention:** the decoder attends to the encoder's outputs (attention from 6.1, between two sequences).
- **ROUGE** measures word overlap with a reference summary. It's useful but blind to meaning: a good paraphrase can score low. You'll meet better evaluation (LLM-as-judge) in Level 7.

## Your turn
1. Swap in `Helsinki-NLP/opus-mt-en-de` (German) or `Helsinki-NLP/opus-mt-en-hi` (Hindi).
2. Summarise a Wikipedia article. What happens when it's longer than the model's max input (1,024 tokens)? Implement "chunk, summarise each chunk, summarise the summaries".
3. Try `google/flan-t5-base` with a prompt like `"summarize: ..."`. One model, many tasks!

## Watch
- Hugging Face LLM course: https://huggingface.co/learn/llm-course/chapter1/1
- Encoder-decoder models explained: https://www.youtube.com/results?search_query=encoder+decoder+transformer+explained+translation
