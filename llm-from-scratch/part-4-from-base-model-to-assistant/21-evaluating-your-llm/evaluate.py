"""Lesson 21: evaluate the base, SFT and DPO models from lessons 19 and 20, four different ways.

  1. perplexity on held-out Shakespeare          (how well does it model text?)
  2. HellaSwag-style multiple choice, by log-likelihood, built from held-out Shakespeare
  3. multiple choice on chat skills, by log-likelihood
  4. generation-based checks: exact match, stopping correctly, greeting style

python evaluate.py                    # ~1-3 min on CPU
python evaluate.py --items 400        # more multiple-choice items = less noisy accuracy
"""
import argparse
import math
import os
import random
from collections import Counter

import torch
import torch.nn.functional as F

from chat_data import TEST_NAMES, TEST_WORDS, greeting_style, test_dataset
from common import DEVICE, answer, load_model, load_shakespeare, render, tok

p = argparse.ArgumentParser()
p.add_argument("--base", default="../19-instruction-tuning-sft-from-scratch/base.pt")
p.add_argument("--sft", default="../19-instruction-tuning-sft-from-scratch/sft.pt")
p.add_argument("--dpo", default="../20-preference-tuning-dpo-from-scratch/dpo.pt")
p.add_argument("--items", type=int, default=200, help="multiple-choice items built from Shakespeare")
args = p.parse_args()

models = {name: load_model(path) for name, path in [("base", args.base), ("sft", args.sft), ("dpo", args.dpo)] if os.path.exists(path)}
if not models:
    raise SystemExit("No models found. Run lesson 19 (pretrain.py, sft.py) and optionally lesson 20 (dpo.py) first.")
print("evaluating:", ", ".join(f"{k} ({v.num_params():,} params)" for k, v in models.items()))
results = {name: {} for name in models}
text = load_shakespeare()
val_text = text[int(0.9 * len(text)):]                        # the 10% no model trained on


# ----------------------------------------------------------------------------- 1. perplexity
@torch.no_grad()
def perplexity(model, s):
    """Cut the text into windows, average the next-character loss, then exp(). Lower is better."""
    ids = torch.tensor(tok.encode(s), device=DEVICE)
    T = model.cfg.block_size
    n = (len(ids) - 1) // T
    x = ids[:n * T].view(n, T)
    y = ids[1:n * T + 1].view(n, T)
    losses = [model(x[i:i + 64], y[i:i + 64])[1] * len(x[i:i + 64]) for i in range(0, n, 64)]
    loss = (torch.stack(losses).sum() / n).item()
    return loss, math.exp(loss)


for name, m in models.items():
    loss, ppl = perplexity(m, val_text)
    results[name]["val loss (nats/char)"] = f"{loss:.3f}"
    results[name]["perplexity"] = f"{ppl:.2f}"
    results[name]["bits per character"] = f"{loss / math.log(2):.2f}"


# ----------------------------------------------------------------------------- 2 + 3. multiple choice by likelihood
@torch.no_grad()
def choice_scores(model, context_ids, endings_ids):
    """For each ending: (sum of log-probs of its tokens, average log-prob per token) given the context."""
    out = []
    for end in endings_ids:
        ids = (context_ids + end)[-model.cfg.block_size - 1:]
        x = torch.tensor([ids[:-1]], device=DEVICE)
        logp = F.log_softmax(model(x)[0][0], dim=-1)            # (T, V)
        targets = torch.tensor(ids[1:], device=DEVICE)
        token_logp = logp[torch.arange(len(targets)), targets][-len(end):]   # only the ending's tokens count
        out.append((token_logp.sum().item(), token_logp.mean().item()))
    return out


def run_mc(items, label):
    for name, m in models.items():
        acc = acc_norm = 0
        for context, endings, correct in items:
            scores = choice_scores(m, context, endings)
            acc += max(range(len(endings)), key=lambda i: scores[i][0]) == correct        # total log-prob
            acc_norm += max(range(len(endings)), key=lambda i: scores[i][1]) == correct   # per-token average
        results[name][f"{label} acc"] = f"{acc / len(items):.0%}"
        results[name][f"{label} acc_norm"] = f"{acc_norm / len(items):.0%}"


rng = random.Random(0)
shakespeare_items = []                                        # "which of these 4 continuations really came next?"
for _ in range(args.items):
    i = rng.randrange(0, len(val_text) - 200)
    context, real = val_text[i:i + 64], val_text[i + 64:i + 96]
    fakes = []
    while len(fakes) < 3:                                     # 3 distractors: 32 characters from elsewhere in val
        j = rng.randrange(0, len(val_text) - 32)
        if abs(j - (i + 64)) > 200:
            fakes.append(val_text[j:j + 32])
    endings = fakes[:]
    correct = rng.randrange(4)
    endings.insert(correct, real)
    shakespeare_items.append((tok.encode(context), [tok.encode(e) for e in endings], correct))
run_mc(shakespeare_items, "Shakespeare MC")

skill_items = []                                              # "which answer would the assistant give?"
for w in TEST_WORDS:
    other = rng.choice([v for v in TEST_WORDS if v != w])
    for prompt, answers in [(f"Uppercase: {w}", [w.upper(), w, w.upper()[::-1], other.upper()]),
                            (f"Spell {w}", ["-".join(w), w, "-".join(w[::-1]), "-".join(other)])]:
        ctx, _ = render(prompt)
        order = list(range(4))
        rng.shuffle(order)
        endings = [tok.encode(answers[k]) + [tok.end] for k in order]
        skill_items.append((ctx, endings, order.index(0)))
run_mc(skill_items, "chat-skill MC")

# ----------------------------------------------------------------------------- 4. generation-based checks
for name, m in models.items():
    tests = test_dataset()
    total = sum(len(v) for v in tests.values())
    exact = sum(answer(m, u) == a for items in tests.values() for u, a in items)
    results[name]["exact match (held-out)"] = f"{exact}/{total}"
    stopped = 0                                               # did it end its reply with <|end|> in time?
    for u, _ in tests["uppercase"]:
        ids, _ = render(u)
        out = m.generate(torch.tensor([ids], device=DEVICE), 40, temperature=1.0, stop_id=tok.end)[0].tolist()
        stopped += out[-1] == tok.end
    results[name]["stops with <|end|>"] = f"{stopped / len(tests['uppercase']):.0%}"
    torch.manual_seed(0)
    styles = Counter(greeting_style(n, answer(m, f"Say hello to {n}.", greedy=False)) for n in TEST_NAMES for _ in range(10))
    results[name]["friendly greetings"] = f"{styles['friendly'] / sum(styles.values()):.0%}"

# ----------------------------------------------------------------------------- report
rows = list(next(iter(results.values())).keys())
print(f"\n{'metric':28s}" + "".join(f"{n:>10s}" for n in models))
for r in rows:
    print(f"{r:28s}" + "".join(f"{results[n][r]:>10s}" for n in models))
print(f"\n(random guessing on 4-way multiple choice = 25%; {len(shakespeare_items)} Shakespeare items, {len(skill_items)} chat-skill items)")
