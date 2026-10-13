"""Project 5.5 part B: fine-tune plain DistilBERT on movie reviews yourself (a plain PyTorch loop, no magic).

python fine_tune.py            # 2,000 IMDB reviews, 1 epoch (~15-25 min on CPU, ~1 min on a GPU)
python fine_tune.py --smoke    # 64 reviews, a few seconds of training
"""
import sys

import torch
from datasets import load_dataset
from torch.utils.data import DataLoader
from transformers import AutoModelForSequenceClassification, AutoTokenizer

SMOKE = "--smoke" in sys.argv
N_TRAIN, N_TEST, MAX_LEN = (64, 32, 64) if SMOKE else (2000, 500, 256)
device = "cuda" if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else "cpu"
torch.manual_seed(0)

# 1. Data: IMDB movie reviews (label 0 = negative, 1 = positive). Shuffle and take a small slice.
imdb = load_dataset("stanfordnlp/imdb")
train = imdb["train"].shuffle(seed=0).select(range(N_TRAIN))
test = imdb["test"].shuffle(seed=0).select(range(N_TEST))

# 2. Tokenizer: text -> token ids the model understands (you'll build one yourself in 5.6!)
tok = AutoTokenizer.from_pretrained("distilbert-base-uncased")
print("Example tokens:", tok.tokenize("Tokenizers split unbelievably long words."))
encode = lambda batch: tok(batch["text"], truncation=True, max_length=MAX_LEN, padding="max_length")
train = train.map(encode, batched=True).with_format("torch", columns=["input_ids", "attention_mask", "label"])
test = test.map(encode, batched=True).with_format("torch", columns=["input_ids", "attention_mask", "label"])

# 3. Model: pretrained DistilBERT body + a NEW 2-class head (randomly initialised -> needs fine-tuning)
model = AutoModelForSequenceClassification.from_pretrained("distilbert-base-uncased", num_labels=2).to(device)
optimizer = torch.optim.AdamW(model.parameters(), lr=3e-5)   # tiny learning rate: nudge, don't wreck, the pretrained knowledge


def accuracy():
    model.eval()
    correct = 0
    with torch.no_grad():
        for b in DataLoader(test, batch_size=32):
            logits = model(input_ids=b["input_ids"].to(device), attention_mask=b["attention_mask"].to(device)).logits
            correct += (logits.argmax(-1).cpu() == b["label"]).sum().item()
    return correct / len(test)


print(f"Accuracy BEFORE fine-tuning: {accuracy():.1%} (coin flip)")
model.train()
for step, b in enumerate(DataLoader(train, batch_size=16, shuffle=True)):
    out = model(input_ids=b["input_ids"].to(device), attention_mask=b["attention_mask"].to(device), labels=b["label"].to(device))
    out.loss.backward()                  # the model computes cross-entropy for us when we pass labels
    optimizer.step(); optimizer.zero_grad()
    if step % 20 == 0:
        print(f"step {step:3d} | loss {out.loss.item():.3f}")
print(f"Accuracy AFTER fine-tuning:  {accuracy():.1%}")

model.save_pretrained("my-sentiment-model"); tok.save_pretrained("my-sentiment-model")
print("Saved to ./my-sentiment-model  ->  pipeline('sentiment-analysis', model='my-sentiment-model')")
