# 6.3 · Fine-tune a small LLM with LoRA

**What you'll build:**
- **Part A:** LoRA from scratch in 20 lines of PyTorch. A small "pretrained" network learns a brand-new task while training only ~4% of its weights. (On real LLMs it's often under 1%.)
- **Part B:** teach a real open LLM (SmolLM2, 135M parameters) to **answer everything like a pirate** 🏴‍☠️ from just 12 examples, using the `peft` library. The test question isn't in the training data, so you'll see it generalise the *style*.

**Like you're 10:** the model is a huge, finished painting. Repainting all of it (full fine-tuning) is slow and expensive. LoRA sticks a thin **transparent sheet** on top and paints only on the sheet. Peel it off and the original is untouched. You can keep different sheets for different jobs.
**Time:** ~2 h · **Builds on:** [6.2 Mini-GPT trained on Shakespeare](../02-mini-gpt-trained-on-shakespeare) · **Needs:** internet for Part B's first run (downloads ~270 MB once), ~2 GB free RAM. No GPU, no API key.

## Why this matters
Prompting changes what you *ask* a model; fine-tuning changes the model itself. Companies fine-tune open models to follow a house style, speak a niche jargon, output a strict format or run cheaply on their own servers. LoRA is the standard way to do it: it needs a fraction of the memory, trains fast, and produces an adapter of a few MB instead of a whole new model. "RAG or fine-tuning?" is a classic interview question, and after this lesson and 7.3 you can answer it from experience.

## What you'll learn
- **Fine-tuning**: continuing to train a pretrained model on your own examples so it changes its behaviour.
- **LoRA (Low-Rank Adaptation)**: freeze the big weight matrix `W` and learn a small update `B @ A` next to it.
- **Rank `r`**: how "thick" the sheet is. Bigger `r` means more capacity and more trainable parameters.
- **Chat templates**: instruction models expect messages wrapped in special tokens, and you must train in the same format.
- **Masking the prompt (`-100`)**: telling the loss to ignore the question so the model only learns to write the answer.

## Before you start
```bash
cd level-6-transformers/03-fine-tune-a-small-llm-with-lora
pip install -r requirements.txt
```
- `torch`: the neural-network library (Part A uses only this).
- `transformers`: downloads and runs SmolLM2 from the Hugging Face Hub.
- `peft`: "parameter-efficient fine-tuning", Hugging Face's LoRA library.

No API key needed. Part B downloads SmolLM2-135M-Instruct (~270 MB) the first time and caches it in `~/.cache/huggingface`.

## Run it
1. From the course root: `cd level-6-transformers/03-fine-tune-a-small-llm-with-lora`
2. Part A, LoRA from scratch: `python lora_from_scratch.py` (10–60 s on a laptop)
3. Part B wiring check, 3 training steps: `python lora_finetune_llm.py --smoke`
4. Part B for real, 120 steps: `python lora_finetune_llm.py` (a few minutes on CPU). It saves the adapter to `./pirate-lora`.

### What you should see
Part A (real output):
```
pretrained on task A, loss 0.000
same model on NEW task B before adapting: loss 529.0
LoRA trains 3,076 of 69,125 parameters (4.4%)
after LoRA fine-tuning on task B: loss 0.018
```
The model is great at task A, terrible at task B (loss 529), then nearly perfect at B after training only 4.4% of its parameters.

Part B (representative output: the course's test machine can't download models, and exact wording and loss values vary between machines and library versions):
```
BEFORE: The tallest mountain on Earth is Mount Everest, located in the Himalayas on the border between Nepal and China. It stands at 8,848 meters (29,029 feet) above sea level.
trainable params: 1,843,200 || all params: 136,358,208 || trainable%: 1.3517
step   0 | loss 3.412
step  20 | loss 1.874
step  40 | loss 0.903
step  60 | loss 0.415
step  80 | loss 0.187
step 100 | loss 0.096

AFTER:  Arr, that be Mount Everest, matey! It stands near 8,848 metres tall in the Himalayas, higher than any crow's nest!
Saved LoRA adapter to ./pirate-lora
```
What to look at:
- **trainable%: 1.35**: only 1.8M of 136M numbers are being trained.
- **The loss falls** as the model learns the pirate style.
- **AFTER** answers a question it never saw in training, in pirate voice, and the fact is still right. It learned a *style*, not a list of answers.
- `pirate-lora/` contains `adapter_model.safetensors`, only a few MB. The original model files are untouched.

## How it works
### Part A: `lora_from_scratch.py`
1. **`LoRALinear`** wraps an existing `nn.Linear` called `base`. It sets `requires_grad = False` on the base weights (frozen), then adds two small trainable matrices: `A` (r × in) with tiny random values and `B` (out × r) full of **zeros**.
2. **`forward()`** returns `base(x) + (x @ A.T @ B.T) * scale`. Because `B` starts at zero, the extra term starts at zero, so the wrapped model behaves exactly like the original until training changes `B`.
3. **"Pretraining"**: a 2-layer network is trained by `fit()` on task A (output = sum of the 256 inputs) for 600 steps until the loss is ~0.
4. **New task B** (sum of the first half minus sum of the second half) scores a loss of 529: the old model is useless for it.
5. **Adapting**: both `Linear` layers are wrapped with `LoRALinear(r=4)`, and `fit()` trains only parameters with `requires_grad=True`, which are just the `A`s and `B`s: 3,076 numbers out of 69,125.

```
x ──► W (frozen, 256×256) ─────────────────┐
  └─► A (4×256) ─► B (256×4) ─► × scale ───┴─► + ─► output
       the small trainable "sheet"
```
Why this works: the *change* a model needs for a new task is usually simple ("low rank"), so `B @ A`, a 256×256 matrix built from just 2,048 numbers, can capture it.

### Part B: `lora_finetune_llm.py`
1. **Load** the tokenizer and model for `MODEL_ID = "HuggingFaceTB/SmolLM2-135M-Instruct"`, and read the 12 question/answer pairs from `pirate_data.jsonl` (one JSON object per line).
2. **`chat(q)`** wraps a question in the model's chat template with `apply_chat_template`. **`ask(q)`** generates a reply with `do_sample=False` (always the most likely token, so BEFORE/AFTER are comparable) and decodes only the new tokens.
3. **BEFORE**: ask "What is the tallest mountain on Earth?", a question that is *not* in the training data.
4. **`get_peft_model(model, LoraConfig(...))`** freezes all 135M weights and adds LoRA sheets to the four attention projections (`q_proj`, `k_proj`, `v_proj`, `o_proj`, the same Wq/Wk/Wv/Wo from 6.1). `r=16` is the rank; `lora_alpha=32` sets the scale (`alpha / r = 2`); `lora_dropout=0.05` randomly drops a few inputs to the sheet during training to reduce overfitting.
5. **Building examples**: each pair becomes `chat(question) + answer + eos_token`. `labels` is a copy of the token ids with the prompt part set to **-100**, the special value PyTorch's loss ignores. The model is graded only on writing the answer and the end-of-text token (so it learns when to stop).
6. **Training loop**: 120 steps, one example per step, cycling through the 12 examples (10 passes). `model(input_ids=..., labels=...)` computes the next-token loss for you, then `backward()` and `optimizer.step()` update only the LoRA weights. `lr=2e-4` is a typical LoRA learning rate.
7. **AFTER + save**: ask the same question again, then `save_pretrained("pirate-lora")` writes only the adapter.

How this scales up: **QLoRA** is LoRA on a model compressed to 4 bits, which is how people fine-tune 7B+ models on one consumer GPU.

## If something goes wrong
- **`OSError: We couldn't connect to 'https://huggingface.co'`** → Part B needs internet the first time to download SmolLM2. Check your connection. Part A works offline.
- **Part B is very slow** → it's running on CPU, which is expected (a few minutes). Close heavy apps, or run it on Google Colab with a GPU. `--smoke` checks the wiring in under a minute.
- **AFTER answer isn't pirate-y yet** → the model hasn't trained enough. Raise `steps` (e.g. 240) or the learning rate to `3e-4`. Results with only 12 examples vary a little from run to run.
- **`ValueError: Target modules {...} not found`** after switching models → other model families name their layers differently. Run `print(model)` and use the names of the attention `Linear` layers you see.
- **`ModuleNotFoundError: No module named 'peft'`** → activate your virtual environment and run `pip install -r requirements.txt`.

## Try this
1. **Thinner sheet.** In Part A, change both `r=4` to `r=1`. How many parameters are trained now, and can it still learn task B?
   <details><summary>Hint</summary>

   It trains 769 parameters (~1.2%) and should still reach a low loss. Task B's change is literally rank 1 ("+1 for the first half, -1 for the second"), so one row and one column are enough. Real fine-tunes need more, which is why `r` is usually 8–64.
   </details>
2. **Rank in Part B.** Change `r=16` to `r=4`, then to `r=64` (keep `lora_alpha = 2 * r`). Compare the trainable parameter counts and the AFTER answers.
   <details><summary>Hint</summary>

   The count scales linearly with `r`: r=4 trains 460,800 parameters, r=16 trains 1,843,200, r=64 trains 7,372,800. With only 12 examples, a bigger `r` doesn't help much and can overfit (it starts repeating training answers word for word).
   </details>
3. **Your own style + reuse the adapter.** Replace `pirate_data.jsonl` with ~20 examples in your own style (for example a study buddy that always ends with a quiz question), train, then load the saved adapter in a *new* script without retraining.
   <details><summary>Solution</summary>

   Each line of the file is `{"q": "...", "a": "..."}`. After training, in a new file:
   ```python
   from peft import PeftModel
   from transformers import AutoModelForCausalLM, AutoTokenizer

   MODEL_ID = "HuggingFaceTB/SmolLM2-135M-Instruct"
   tok = AutoTokenizer.from_pretrained(MODEL_ID)
   base = AutoModelForCausalLM.from_pretrained(MODEL_ID)
   model = PeftModel.from_pretrained(base, "pirate-lora")   # stick the saved sheet back on
   model.eval()

   prompt = tok.apply_chat_template([{"role": "user", "content": "How do plants grow?"}],
                                    tokenize=False, add_generation_prompt=True)
   ids = tok(prompt, return_tensors="pt")
   out = model.generate(**ids, max_new_tokens=60, do_sample=False)
   print(tok.decode(out[0][ids["input_ids"].shape[1]:], skip_special_tokens=True))
   ```
   You can keep several adapters (`pirate-lora`, `study-buddy-lora`) for one base model and swap them in seconds.
   </details>

## Check yourself
1. Why does `B` start at zero instead of random numbers?
2. What would go wrong if you didn't set the prompt's labels to -100?
3. Your company wants the model to answer from its 500-page handbook, which changes every month. Is LoRA fine-tuning the right tool? What would you use?
4. Why is a LoRA adapter only a few MB when the model is hundreds of MB?

<details><summary>Answers</summary>

1. So that `B @ A = 0` at the start: the wrapped model behaves exactly like the pretrained one, and training starts from what it already knows instead of from random damage.
2. The model would also be trained to produce the *question* and the chat-template tokens, wasting capacity on text it will never need to write, and it can start echoing questions back.
3. No. Fine-tuning is good for *style and format*, but bad for facts that change often (you'd retrain every month, and it can still make things up). Use RAG (7.3): look up the relevant handbook pages at question time and give them to the model.
4. It stores only the small `A` and `B` matrices (1.8M numbers here), not the 135M frozen weights, which stay in the original model files.
</details>

## Learn more (optional)
- LoRA explained: https://www.youtube.com/results?search_query=LoRA+low+rank+adaptation+explained
- Hugging Face PEFT docs: https://huggingface.co/docs/peft/index
- Original LoRA paper (readable abstract): https://arxiv.org/abs/2106.09685

## Next
→ [6.4 · Translator & summariser with Hugging Face](../04-translator-and-summarizer-with-huggingface)
