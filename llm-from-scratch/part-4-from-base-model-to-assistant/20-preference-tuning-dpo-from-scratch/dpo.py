"""Lesson 20: Direct Preference Optimization (DPO) from scratch.

Lesson 19's model greets people in two styles (friendly and grumpy) because its SFT data had both.
We show it PAIRS: for the same prompt, a chosen (friendly) and a rejected (grumpy) answer,
and DPO shifts probability toward the chosen style, while a frozen reference model keeps it
from drifting too far.

python dpo.py                                 # needs ../19-instruction-tuning-sft-from-scratch/sft.pt
python dpo.py --beta 0.5 --steps 150
"""
import argparse
import copy
import os
import random
import time
from collections import Counter

import torch
import torch.nn.functional as F

from chat_data import TEST_NAMES, TRAIN_NAMES, greeting_style, polite_greeting, rude_greeting, test_dataset
from common import IGNORE, answer, load_model, make_batch, save_model

p = argparse.ArgumentParser()
p.add_argument("--sft", default="../19-instruction-tuning-sft-from-scratch/sft.pt")
p.add_argument("--beta", type=float, default=0.1, help="how strongly to stay close to the reference model (smaller = freer)")
p.add_argument("--steps", type=int, default=100)
p.add_argument("--lr", type=float, default=1e-4)
args = p.parse_args()
if not os.path.exists(args.sft):
    raise SystemExit(f"{args.sft} not found. Run lesson 19 first (python pretrain.py, then python sft.py).")
torch.manual_seed(1337)


def report(model, title):
    print(f"\n{title}")
    torch.manual_seed(0)
    styles = Counter(greeting_style(n, answer(model, f"Say hello to {n}.", greedy=False)) for n in TEST_NAMES for _ in range(10))
    total = sum(styles.values())
    print(f"   greetings to {len(TEST_NAMES)} new names x 10 samples: "
          + ", ".join(f"{k} {v / total:.0%}" for k, v in sorted(styles.items())))
    skills = test_dataset()
    correct = sum(answer(model, u) == a for items in skills.values() for u, a in items)
    print(f"   other skills still correct: {correct}/{sum(len(v) for v in skills.values())}")


def sequence_logprob(model, pairs):
    """log p(answer | prompt) for each (prompt, answer): the SUM of the log-probabilities of the answer's tokens.
    make_batch already marks non-answer targets with IGNORE, so we just add up the rest."""
    x, y = make_batch(pairs, model.cfg.block_size)
    logp = F.log_softmax(model(x)[0], dim=-1)                              # (B, T, V)
    mask = y != IGNORE
    token_logp = logp.gather(-1, y.clamp(min=0).unsqueeze(-1)).squeeze(-1)  # log-prob of each target token
    return (token_logp * mask).sum(dim=1)                                  # (B,)


policy = load_model(args.sft)                     # the model we train (π, "pi")
reference = copy.deepcopy(policy).eval()          # a frozen copy of the SFT model (π_ref)
for prm in reference.parameters():
    prm.requires_grad_(False)

prefs = [(f"Say hello to {n}.", polite_greeting(n), rude_greeting(n)) for n in TRAIN_NAMES]   # (prompt, chosen, rejected)
print(f"{len(prefs)} preference pairs, e.g. {prefs[0]}")
report(policy, "BEFORE DPO (the SFT model):")

opt = torch.optim.AdamW(policy.parameters(), lr=args.lr, weight_decay=0.0)
policy.train()
rng = random.Random(0)
t0 = time.time()
print(f"\ntraining: beta {args.beta}, {args.steps} steps, 16 pairs per step")
for step in range(1, args.steps + 1):
    batch = rng.sample(prefs, 16)
    chosen = [(q, c) for q, c, _ in batch]
    rejected = [(q, r) for q, _, r in batch]
    pi_c, pi_r = sequence_logprob(policy, chosen), sequence_logprob(policy, rejected)
    with torch.no_grad():
        ref_c, ref_r = sequence_logprob(reference, chosen), sequence_logprob(reference, rejected)
    # "implicit rewards": how much MORE likely the policy makes an answer than the reference does
    reward_c = args.beta * (pi_c - ref_c)
    reward_r = args.beta * (pi_r - ref_r)
    loss = -F.logsigmoid(reward_c - reward_r).mean()                      # the whole DPO loss
    opt.zero_grad(set_to_none=True)
    loss.backward()
    torch.nn.utils.clip_grad_norm_(policy.parameters(), 1.0)
    opt.step()
    if step % 20 == 0 or step == 1:
        acc = (reward_c > reward_r).float().mean().item()
        print(f"step {step:4d} | loss {loss.item():.3f} | reward chosen {reward_c.mean().item():+.2f} "
              f"| reward rejected {reward_r.mean().item():+.2f} | margin {(reward_c - reward_r).mean().item():+.2f} "
              f"| pairs ranked right {acc:.0%} | {time.time() - t0:.0f}s")

policy.eval()
save_model(policy, "dpo.pt")
print("saved dpo.pt")
report(policy, "AFTER DPO:")
for n in TEST_NAMES[:3]:
    print(f"   USER: Say hello to {n}.   ASSISTANT: {answer(policy, f'Say hello to {n}.', greedy=False)!r}")
