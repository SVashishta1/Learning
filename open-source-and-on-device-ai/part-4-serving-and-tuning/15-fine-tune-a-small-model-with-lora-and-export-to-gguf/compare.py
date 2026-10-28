"""Step 2: ask the same questions before and after fine-tuning, side by side.

Run:  python compare.py
"""
import os

import torch
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer

BASE = os.environ.get("BASE_MODEL", "Qwen/Qwen2.5-0.5B-Instruct")
SYSTEM = "You are Sprout, the friendly plant-care helper."       # the same system message as in training
QUESTIONS = ["Who are you?",
             "My cactus is turning soft and brown at the bottom. What should I do?",   # not in the training data
             "What is the tallest mountain in the world?"]                            # off-topic on purpose

tokenizer = AutoTokenizer.from_pretrained(BASE)
model = AutoModelForCausalLM.from_pretrained(BASE, dtype=torch.float32)
model = PeftModel.from_pretrained(model, "sprout-lora")          # base model + the LoRA patches


def answer(question):
    messages = [{"role": "system", "content": SYSTEM}, {"role": "user", "content": question}]
    ids = tokenizer.apply_chat_template(messages, add_generation_prompt=True, return_tensors="pt",
                                        return_dict=True)
    with torch.no_grad():
        out = model.generate(**ids, max_new_tokens=120, do_sample=False)   # do_sample=False: same answer every time
    return tokenizer.decode(out[0][ids["input_ids"].shape[1]:], skip_special_tokens=True).strip()


for question in QUESTIONS:
    print(f"\n❓ {question}")
    with model.disable_adapter():                                  # temporarily switch the patches off
        print(f"   BEFORE: {answer(question)}")
    print(f"   AFTER:  {answer(question)}")
