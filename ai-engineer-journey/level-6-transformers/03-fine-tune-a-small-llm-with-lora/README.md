# 6.3 · Fine-tune a small LLM with LoRA

**What you build:**
- **Part A:** LoRA from scratch in 20 lines. You see a "pretrained" model adapt to a new task while training only a few percent of its weights.
- **Part B:** teach a real open LLM (SmolLM2, 135M parameters) to **answer everything like a pirate** 🏴‍☠️ from just 12 examples, using the `peft` library. The question at the end isn't in the training data, so you'll see it generalise the *style*.

**Like you're 10:** the model is a huge, finished painting. Repainting it all (full fine-tuning) is slow and expensive. LoRA sticks a thin **transparent sheet** on top and paints only on the sheet. Peel it off and the original is untouched. You can keep different sheets for different jobs.

## Run it
```bash
cd level-6-transformers/03-fine-tune-a-small-llm-with-lora
pip install -r requirements.txt
python lora_from_scratch.py               # part A, seconds
python lora_finetune_llm.py --smoke       # part B wiring check (downloads ~270 MB once)
python lora_finetune_llm.py               # part B, a few minutes on CPU
```

## Key ideas
- **Why LoRA:** a model's weight updates during fine-tuning are "low-rank", so a small `B @ A` captures most of the change. You train ~1% of the parameters, use far less memory, and the result is a tiny adapter file.
- **`r` (rank):** the sheet's "thickness". Bigger r means more capacity but more parameters (common values: 8–64).
- **Chat template:** instruction models expect a specific format with special tokens. Always use `tok.apply_chat_template`.
- **Masking the prompt (`-100`):** we only teach the model to produce the answer, not to repeat the question.
- **QLoRA** = LoRA on a 4-bit compressed model; it's how people fine-tune 7B+ models on a single consumer GPU.

## Your turn
1. Write 20 examples in *your* style (a study buddy that always gives a quiz question at the end) and fine-tune.
2. Change `r` to 4 and to 64. Compare the trainable parameter counts and the results.
3. Load the adapter later: `PeftModel.from_pretrained(base_model, "pirate-lora")`.

## Watch
- LoRA explained: https://www.youtube.com/results?search_query=LoRA+low+rank+adaptation+explained
- Hugging Face PEFT docs: https://huggingface.co/docs/peft/index
- Original LoRA paper (readable abstract): https://arxiv.org/abs/2106.09685
