"""Capstone stage 4: supervised fine-tuning on conversations (lesson 19), loss on assistant tokens only.

python sft.py              # loads base.pt -> chat.pt (~3-8 min on CPU)
"""
import argparse
import random
import time

import torch

from chat_data import sft_conversations, test_questions
from common import DEVICE, IGNORE, load_model, load_tokenizer, render_conversation, reply, save_model

p = argparse.ArgumentParser()
p.add_argument("--steps", type=int, default=800)
p.add_argument("--lr", type=float, default=1e-3)
args = p.parse_args()
torch.manual_seed(1337)
tok = load_tokenizer()
model = load_model("base.pt")
T = model.cfg.block_size


def make_batch(convs):
    x = torch.full((len(convs), T), tok.end, dtype=torch.long)
    y = torch.full((len(convs), T), IGNORE, dtype=torch.long)
    for r, conv in enumerate(convs):
        ids, train = render_conversation(tok, conv)
        ids, train = ids[:T + 1], train[:T + 1]
        n = len(ids) - 1
        x[r, :n] = torch.tensor(ids[:-1])
        y[r, :n] = torch.tensor([t if keep else IGNORE for t, keep in zip(ids[1:], train[1:])])
    return x.to(DEVICE), y.to(DEVICE)


def test(title):
    torch.manual_seed(0)
    tests = test_questions()
    hits = 0
    for q, key in tests:
        a, _ = reply(model, tok, [], q, temperature=0.3)
        hits += key.lower() in a.lower()
    print(f"{title}: {hits}/{len(tests)} held-out questions answered correctly")
    for q in ["Who are you?", "Which is the largest ocean on Earth?", "Say hello to Kenji."]:
        print(f"   USER: {q}\n   BOT:  {reply(model, tok, [], q, temperature=0.3)[0]}")


test("base model")
convs = sft_conversations()
opt = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=0.0)
rng = random.Random(0)
model.train()
t0 = time.time()
print(f"SFT on {len(convs)} conversations for {args.steps} steps")
for step in range(1, args.steps + 1):
    _, loss = model(*make_batch(rng.sample(convs, 32)))
    opt.zero_grad(set_to_none=True)
    loss.backward()
    torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
    opt.step()
    if step % 100 == 0:
        print(f"step {step:4d} | loss {loss.item():.3f} | {time.time() - t0:.0f}s")
model.eval()
save_model(model, "chat.pt")
print("saved chat.pt")
test("chat model")
