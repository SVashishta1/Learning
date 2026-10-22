# Level 6 · Transformers: a model that pays attention

In 2017 the paper *"Attention Is All You Need"* introduced the transformer. Every modern LLM (GPT, Claude, Llama) is a transformer. In this level you hand-code attention, build and train a mini-GPT, fine-tune a real model cheaply with LoRA, use Hugging Face for translation and summarisation, and run an open LLM on your own laptop.

| # | Project | Idea |
|---|---------|------|
| 6.1 | [Self-attention by hand](01-self-attention-by-hand-numpy) | queries, keys, values, causal masking, multi-head |
| 6.2 | [Mini-GPT on Shakespeare](02-mini-gpt-trained-on-shakespeare) | a full GPT you train yourself |
| 6.3 | [Fine-tune with LoRA](03-fine-tune-a-small-llm-with-lora) | adapt a real LLM by training <1% of its weights |
| 6.4 | [Translator & summariser](04-translator-and-summarizer-with-huggingface) | encoder-decoder models, pipelines, ROUGE |
| 6.5 | [Run an open LLM locally](05-run-an-open-llm-on-your-laptop) | Ollama, chat templates, local vs. API trade-offs |

**Watch first (seriously, it'll make everything click):**
- 3Blue1Brown, "Transformers, the tech behind LLMs" and "Attention in transformers, step-by-step": https://www.youtube.com/playlist?list=PLZHQObOWTQDNU6R1_67000Dx_ZCJB-3pi
- Karpathy, "Let's build GPT: from scratch, in code, spelled out": https://www.youtube.com/watch?v=kCc8FmEb1nY

**Before you start:** 6.1 runs anywhere in a second. 6.2 and 6.3 train models: on a laptop CPU expect roughly 15–60 minutes for the full runs (each has a quick `--smoke` check first), or use a free GPU on Google Colab. 6.4 and 6.5 download pretrained models (0.3–2 GB) the first time. No API key is needed in this level.

**Start here →** [6.1 · Self-attention by hand](01-self-attention-by-hand-numpy)

**Go deeper:** the [llm-from-scratch](../../llm-from-scratch) course rebuilds this level step by step alongside every video of Karpathy's *Neural Networks: Zero to Hero*, all the way to training your own tiny ChatGPT.
