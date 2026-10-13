"""A small GPT (decoder-only transformer), the same architecture as GPT-2, just tiny.
Read top to bottom: Head -> MultiHead -> FeedForward -> Block -> GPT."""
from dataclasses import dataclass

import torch
from torch import nn
from torch.nn import functional as F


@dataclass
class Config:
    vocab_size: int = 65
    block_size: int = 128      # context length: how many previous characters the model can see
    n_embd: int = 192          # size of each token's vector
    n_head: int = 6
    n_layer: int = 6
    dropout: float = 0.1


class CausalSelfAttention(nn.Module):
    """Project 6.1, but batched, trainable, and with all heads computed at once."""
    def __init__(self, c: Config):
        super().__init__()
        self.qkv = nn.Linear(c.n_embd, 3 * c.n_embd)   # Wq, Wk, Wv for every head in one matrix
        self.proj = nn.Linear(c.n_embd, c.n_embd)      # Wo
        self.n_head, self.drop = c.n_head, nn.Dropout(c.dropout)
        self.register_buffer("mask", torch.tril(torch.ones(c.block_size, c.block_size)).bool())

    def forward(self, x):
        B, T, C = x.shape
        q, k, v = self.qkv(x).split(C, dim=2)
        # (B, T, C) -> (B, heads, T, head_size)
        q, k, v = (t.view(B, T, self.n_head, C // self.n_head).transpose(1, 2) for t in (q, k, v))
        att = (q @ k.transpose(-2, -1)) / (k.size(-1) ** 0.5)
        att = att.masked_fill(~self.mask[:T, :T], float("-inf"))   # no peeking at the future
        att = self.drop(F.softmax(att, dim=-1))
        y = (att @ v).transpose(1, 2).contiguous().view(B, T, C)   # glue the heads back together
        return self.drop(self.proj(y))


class FeedForward(nn.Module):
    """After words 'talk' (attention), each word 'thinks' on its own (a small MLP)."""
    def __init__(self, c: Config):
        super().__init__()
        self.net = nn.Sequential(nn.Linear(c.n_embd, 4 * c.n_embd), nn.GELU(), nn.Linear(4 * c.n_embd, c.n_embd), nn.Dropout(c.dropout))

    def forward(self, x):
        return self.net(x)


class Block(nn.Module):
    def __init__(self, c: Config):
        super().__init__()
        self.ln1, self.attn = nn.LayerNorm(c.n_embd), CausalSelfAttention(c)
        self.ln2, self.ffwd = nn.LayerNorm(c.n_embd), FeedForward(c)

    def forward(self, x):
        x = x + self.attn(self.ln1(x))     # "+ x" = residual connection: an information highway for deep nets
        x = x + self.ffwd(self.ln2(x))
        return x


class GPT(nn.Module):
    def __init__(self, c: Config):
        super().__init__()
        self.c = c
        self.tok_emb = nn.Embedding(c.vocab_size, c.n_embd)   # WHAT the token is
        self.pos_emb = nn.Embedding(c.block_size, c.n_embd)   # WHERE it is (attention alone ignores order!)
        self.blocks = nn.Sequential(*[Block(c) for _ in range(c.n_layer)])
        self.ln_f = nn.LayerNorm(c.n_embd)
        self.head = nn.Linear(c.n_embd, c.vocab_size)

    def forward(self, idx, targets=None):
        B, T = idx.shape
        x = self.tok_emb(idx) + self.pos_emb(torch.arange(T, device=idx.device))
        logits = self.head(self.ln_f(self.blocks(x)))          # (B, T, vocab): next-token scores at every position
        loss = None if targets is None else F.cross_entropy(logits.view(-1, logits.size(-1)), targets.view(-1))
        return logits, loss

    @torch.no_grad()
    def generate(self, idx, max_new_tokens, temperature=0.8, top_k=None):
        for _ in range(max_new_tokens):
            logits, _ = self(idx[:, -self.c.block_size:])       # only the last block_size tokens fit
            logits = logits[:, -1, :] / temperature
            if top_k:
                v, _ = torch.topk(logits, top_k)
                logits[logits < v[:, [-1]]] = float("-inf")     # only sample from the k most likely
            nxt = torch.multinomial(F.softmax(logits, dim=-1), 1)
            idx = torch.cat([idx, nxt], dim=1)
        return idx
