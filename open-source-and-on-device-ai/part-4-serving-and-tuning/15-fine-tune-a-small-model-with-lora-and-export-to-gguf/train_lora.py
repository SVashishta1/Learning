"""Step 1: teach a small model a new style with LoRA (only ~1% of its weights get trained).

Run:  python train_lora.py
Makes: sprout-lora/   (the LoRA adapter: a few MB of "patches" for the base model)
Takes ~20-60 min on a laptop CPU, ~1-2 min on a GPU (also works on a free Colab GPU).
"""
import os

import torch
from datasets import load_dataset
from peft import LoraConfig
from transformers import AutoModelForCausalLM, AutoTokenizer
from trl import SFTConfig, SFTTrainer

BASE = os.environ.get("BASE_MODEL", "Qwen/Qwen2.5-0.5B-Instruct")   # ~1 GB download, Apache 2.0 licence
OUT = "sprout-lora"

dataset = load_dataset("json", data_files="plant_chat.jsonl", split="train")   # 48 example chats
print(f"📚 {len(dataset)} example conversations, e.g.:\n{dataset[0]['messages'][1]['content']}\n"
      f"→ {dataset[0]['messages'][2]['content']}\n")

tokenizer = AutoTokenizer.from_pretrained(BASE)
model = AutoModelForCausalLM.from_pretrained(BASE, dtype=torch.float32)  # float32: safe on every CPU

# LoRA: freeze the original weights, and next to each chosen layer add two thin matrices (A and B)
# that learn a small correction. Only A and B are trained.
lora = LoraConfig(
    r=16,                         # rank: how "wide" the correction is (8-64 is common)
    lora_alpha=32,                # strength of the correction (often 2 x r)
    lora_dropout=0.05,            # randomly ignore 5% during training, so it doesn't just memorise
    target_modules="all-linear",  # add LoRA to every linear layer (attention and MLP)
    task_type="CAUSAL_LM",        # a model that predicts the next token
)

settings = SFTConfig(
    output_dir=OUT,
    num_train_epochs=3,                   # read the whole dataset 3 times
    per_device_train_batch_size=4,        # 4 conversations per step
    learning_rate=2e-4,                   # LoRA likes a higher learning rate than full fine-tuning
    lr_scheduler_type="cosine",           # start fast, slow down gently towards the end
    warmup_steps=3,
    logging_steps=4,                      # print the loss every 4 steps
    max_length=512,                       # our chats are short; longer ones would be cut here
    save_strategy="no",                   # we save once, at the end
    report_to="none",                     # no online dashboards
    bf16=torch.cuda.is_available() and torch.cuda.is_bf16_supported(),   # 16-bit maths only on GPUs that can
)

trainer = SFTTrainer(model=model, args=settings, train_dataset=dataset,
                     processing_class=tokenizer, peft_config=lora)
trainer.model.print_trainable_parameters()   # shows how few weights LoRA trains
trainer.train()
trainer.save_model(OUT)                      # saves only the adapter (and the tokenizer)
print(f"\n✅ Saved the LoRA adapter in {OUT}/")
