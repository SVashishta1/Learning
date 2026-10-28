"""Shared pieces for lessons 19-21: the tokenizer with chat special tokens, the chat template,
loss masking, loading/saving models, and answering a prompt.

The chat template (what the model actually reads):
    <|user|>Uppercase: apple<|end|><|assistant|>APPLE<|end|>
"""
import os
import urllib.request

import torch

from model import GPT, Config

SHAKESPEARE_URL = "https://raw.githubusercontent.com/karpathy/char-rnn/master/data/tinyshakespeare/input.txt"
DEVICE = "cuda" if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else "cpu"
IGNORE = -100                     # F.cross_entropy skips targets equal to -100: "no loss here"


class ChatTokenizer:
    """One token per character (newline + the 95 printable ASCII characters), plus 3 special tokens
    that no typed text can produce: <|user|>, <|assistant|>, <|end|>."""

    SPECIALS = ["<|user|>", "<|assistant|>", "<|end|>"]

    def __init__(self):
        self.chars = ["\n"] + [chr(i) for i in range(32, 127)]
        self.stoi = {c: i for i, c in enumerate(self.chars)}
        n = len(self.chars)
        self.special = {s: n + i for i, s in enumerate(self.SPECIALS)}       # 96, 97, 98
        self.user, self.assistant, self.end = (self.special[s] for s in self.SPECIALS)
        self.vocab_size = n + len(self.SPECIALS)

    def encode(self, text):
        return [self.stoi[c] for c in text if c in self.stoi]              # unknown characters are skipped

    def decode(self, ids):
        inv = {v: k for k, v in self.special.items()}                      # 96 -> "<|user|>", ...
        return "".join(inv[i] if i in inv else self.chars[i] for i in ids)


tok = ChatTokenizer()


def render(user, assistant=None):
    """Turn one exchange into token ids, plus a mask saying which TARGETS are trained on.
    Only the assistant's reply and its closing <|end|> get loss: we teach the model to answer,
    not to imitate the user."""
    ids = [tok.user] + tok.encode(user) + [tok.end, tok.assistant]
    train = [False] * len(ids)
    if assistant is not None:
        reply = tok.encode(assistant) + [tok.end]
        ids += reply
        train += [True] * len(reply)
    return ids, train


def make_batch(pairs, block_size, mask_user=True):
    """pairs: list of (user, assistant). Returns x, y of shape (B, T) where y = x shifted by one,
    and every y position that is not part of an assistant reply is set to IGNORE (loss masking).
    mask_user=False trains on every real token (only padding is ignored), for comparison."""
    rows = [render(u, a) for u, a in pairs]
    T = min(block_size, max(len(ids) for ids, _ in rows) - 1)
    x = torch.full((len(rows), T), tok.end, dtype=torch.long)              # padding: any id, it is never trained
    y = torch.full((len(rows), T), IGNORE, dtype=torch.long)
    for r, (ids, train) in enumerate(rows):
        ids, train = ids[:T + 1], train[:T + 1]
        n = len(ids) - 1
        x[r, :n] = torch.tensor(ids[:-1])
        y[r, :n] = torch.tensor([t if keep or not mask_user else IGNORE for t, keep in zip(ids[1:], train[1:])])
    return x.to(DEVICE), y.to(DEVICE)


def load_shakespeare():
    if not os.path.exists("input.txt"):
        urllib.request.urlretrieve(SHAKESPEARE_URL, "input.txt")
    return open("input.txt", encoding="utf-8").read()


def save_model(model, path):
    torch.save({"model": model.state_dict(), "config": model.cfg.__dict__}, path)


def load_model(path):
    if not os.path.exists(path):
        raise SystemExit(f"{path} not found. See 'Run it' in this lesson's README for which script creates it.")
    ckpt = torch.load(path, map_location="cpu")
    model = GPT(Config(**ckpt["config"])).to(DEVICE)
    model.load_state_dict(ckpt["model"])
    return model.eval()


@torch.no_grad()
def answer(model, user, max_new_tokens=60, temperature=1.0, greedy=True):
    """Ask the model one question with the chat template and return its reply (text before <|end|>)."""
    ids, _ = render(user)
    idx = torch.tensor([ids], device=DEVICE)
    out = []
    for _ in range(max_new_tokens):
        logits, _ = model(idx[:, -model.cfg.block_size:])
        logits = logits[:, -1, :]
        if greedy:
            nxt = logits.argmax(dim=-1, keepdim=True)
        else:
            nxt = torch.multinomial(torch.softmax(logits / temperature, dim=-1), 1)
        if nxt.item() == tok.end:
            break
        out.append(nxt.item())
        idx = torch.cat([idx, nxt], dim=1)
    return tok.decode(out)
