"""Lesson 19, step 2: supervised fine-tuning (SFT). Teach the base model to answer in the chat format.

python sft.py                 # loads base.pt, 600 steps (~2-5 min on CPU) -> sft.pt
python sft.py --no-mask       # experiment: also train on the user's tokens (see README "Try this")
"""
import argparse
import random
import time
from collections import Counter

import torch

from chat_data import TEST_NAMES, greeting_style, sft_dataset, test_dataset
from common import answer, load_model, make_batch, save_model

p = argparse.ArgumentParser()
p.add_argument("--steps", type=int, default=600)
p.add_argument("--lr", type=float, default=5e-4)
p.add_argument("--no-mask", action="store_true", help="train on every token, not only the assistant's")
args = p.parse_args()
torch.manual_seed(1337)


def evaluate(model, title):
    """Exact-match accuracy per skill on held-out prompts (greedy), and the style of greetings (sampled)."""
    print(f"\n{title}")
    for skill, items in test_dataset().items():
        correct = sum(answer(model, u) == a for u, a in items)
        print(f"   {skill:14s} {correct:3d}/{len(items):3d} correct")
    torch.manual_seed(0)
    styles = Counter(greeting_style(n, answer(model, f"Say hello to {n}.", greedy=False)) for n in TEST_NAMES for _ in range(5))
    print("   greetings to new names (5 samples each):", dict(styles))


def show(model, title):
    print(f"\n{title}")
    for q in ["Uppercase: lantern", "Spell coral", "Say hello to Priya.", "Who are you?"]:
        print(f"   USER: {q:22s} ASSISTANT: {answer(model, q)!r}")


model = load_model("base.pt")
show(model, "BEFORE SFT (the base model just continues text in Shakespeare style):")
evaluate(model, "BEFORE SFT, held-out test:")

data = sft_dataset()
print(f"\ntraining on {len(data)} conversations, {args.steps} steps, loss on {'ALL tokens' if args.no_mask else 'assistant tokens only'}")
x, y = make_batch(data[:1], model.cfg.block_size)
print("one training row  x:", x[0].tolist()[:40], "...")
print("                  y:", y[0].tolist()[:40], "...  (-100 = no loss)")

opt = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=0.0)
model.train()
rng = random.Random(0)
t0 = time.time()
for step in range(1, args.steps + 1):
    x, y = make_batch(rng.sample(data, 32), model.cfg.block_size, mask_user=not args.no_mask)
    _, loss = model(x, y)
    opt.zero_grad(set_to_none=True)
    loss.backward()
    torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
    opt.step()
    if step % 100 == 0:
        print(f"step {step:4d} | loss {loss.item():.3f} | {time.time() - t0:.0f}s")

model.eval()
save_model(model, "sft.pt")
print("saved sft.pt")
show(model, "AFTER SFT:")
evaluate(model, "AFTER SFT, held-out test:")
