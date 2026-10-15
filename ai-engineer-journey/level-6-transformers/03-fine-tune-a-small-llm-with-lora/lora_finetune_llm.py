"""Project 6.3 part B: teach a real 135M-parameter LLM to answer like a pirate, using LoRA (peft).

python lora_finetune_llm.py           # ~3-8 min on CPU
python lora_finetune_llm.py --smoke   # 3 training steps
"""
import json
import sys

import torch
from peft import LoraConfig, get_peft_model
from transformers import AutoModelForCausalLM, AutoTokenizer

SMOKE = "--smoke" in sys.argv
MODEL_ID = "HuggingFaceTB/SmolLM2-135M-Instruct"       # small, open, instruction-tuned (~270 MB)
torch.manual_seed(0)

tok = AutoTokenizer.from_pretrained(MODEL_ID)
model = AutoModelForCausalLM.from_pretrained(MODEL_ID)
data = [json.loads(line) for line in open("pirate_data.jsonl", encoding="utf-8")]


def chat(q):
    return tok.apply_chat_template([{"role": "user", "content": q}], tokenize=False, add_generation_prompt=True)


def ask(q, max_new_tokens=60):
    ids = tok(chat(q), return_tensors="pt")
    out = model.generate(**ids, max_new_tokens=max_new_tokens, do_sample=False)
    return tok.decode(out[0][ids["input_ids"].shape[1]:], skip_special_tokens=True).strip()


question = "What is the tallest mountain on Earth?"        # NOT in the training data
print("BEFORE:", ask(question))

# LoRA adapters on the attention projections only
model = get_peft_model(model, LoraConfig(r=16, lora_alpha=32, lora_dropout=0.05,
                                         target_modules=["q_proj", "k_proj", "v_proj", "o_proj"], task_type="CAUSAL_LM"))
model.print_trainable_parameters()

examples = []
for ex in data:
    prompt = chat(ex["q"])
    full = prompt + ex["a"] + tok.eos_token
    ids = tok(full, return_tensors="pt")["input_ids"][0]
    labels = ids.clone()
    labels[:len(tok(prompt)["input_ids"])] = -100           # only learn the ANSWER, not the question
    examples.append((ids, labels))

optimizer = torch.optim.AdamW([p for p in model.parameters() if p.requires_grad], lr=2e-4)
model.train()
steps = 3 if SMOKE else 120
for step in range(steps):
    ids, labels = examples[step % len(examples)]
    loss = model(input_ids=ids.unsqueeze(0), labels=labels.unsqueeze(0)).loss
    loss.backward(); optimizer.step(); optimizer.zero_grad()
    if step % 20 == 0:
        print(f"step {step:3d} | loss {loss.item():.3f}")

model.eval()
print("\nAFTER: ", ask(question))
model.save_pretrained("pirate-lora")     # saves ONLY the adapter: a few MB instead of the whole model
print("Saved LoRA adapter to ./pirate-lora")
