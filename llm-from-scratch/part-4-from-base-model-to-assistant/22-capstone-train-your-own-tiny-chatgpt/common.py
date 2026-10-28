"""Shared by every stage of the capstone: paths, the tokenizer with chat tokens, the chat template,
loading/saving models and generating a reply.

Chat template for a whole conversation (several turns):
    <|user|>Hi!<|end|><|assistant|>Hello! How can I help you today?<|end|><|user|>...<|end|><|assistant|>
"""
import os

import torch

from bpe import RegexTokenizer
from model import GPT, Config

DATA = "data"
TOKENIZER_FILE = os.path.join(DATA, "tok.model")
DEVICE = "cuda" if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else "cpu"
IGNORE = -100
SPECIALS = ["<|endoftext|>", "<|user|>", "<|assistant|>", "<|end|>"]


def load_tokenizer():
    if not os.path.exists(TOKENIZER_FILE):
        raise SystemExit(f"{TOKENIZER_FILE} not found: run `python tokenizer.py` first.")
    tok = RegexTokenizer().load(TOKENIZER_FILE)
    tok.eot, tok.user, tok.assistant, tok.end = (tok.special_tokens[s] for s in SPECIALS)
    tok.vocab_size = max(tok.vocab) + 1
    return tok


def render_conversation(tok, turns):
    """turns: [(role, text), ...] with role 'user' or 'assistant'.
    Returns token ids and, for each id, True if it belongs to an assistant reply (those get loss in SFT)."""
    ids, train = [], []
    for role, text in turns:
        if role == "user":
            part = [tok.user] + tok.encode_ordinary(text) + [tok.end]
            ids += part
            train += [False] * len(part)
        else:
            ids.append(tok.assistant)
            train.append(False)
            part = tok.encode_ordinary(text) + [tok.end]          # the model must learn to say <|end|> too
            ids += part
            train += [True] * len(part)
    return ids, train


def save_model(model, path):
    torch.save({"model": model.state_dict(), "config": model.cfg.__dict__}, path)


def load_model(path):
    if not os.path.exists(path):
        raise SystemExit(f"{path} not found. Run the earlier stages first (see README).")
    ckpt = torch.load(path, map_location="cpu")
    model = GPT(Config(**ckpt["config"])).to(DEVICE)
    model.load_state_dict(ckpt["model"])
    return model.eval()


@torch.no_grad()
def reply(model, tok, history, user_message, temperature=0.7, top_k=20, max_new_tokens=60):
    """Add the user's message to the history, let the assistant answer, return (answer, new history)."""
    turns = history + [("user", user_message)]
    ids, _ = render_conversation(tok, turns)
    ids = ids + [tok.assistant]
    idx = torch.tensor([ids[-model.cfg.block_size:]], device=DEVICE)   # keep only what fits in the context
    out = model.generate(idx, max_new_tokens, temperature=temperature, top_k=top_k, stop_id=tok.end)[0].tolist()
    new = out[idx.size(1):]
    if new and new[-1] == tok.end:
        new = new[:-1]
    text = tok.decode(new).strip()
    return text, turns + [("assistant", text)]
