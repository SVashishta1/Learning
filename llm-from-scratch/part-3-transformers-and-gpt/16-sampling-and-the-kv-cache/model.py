"""Lesson 14's GPT (same weight names, so lesson 14's ckpt.pt loads), plus two additions:
  * a KV cache: remember every layer's keys and values so each new token costs one token of work
  * sampling filters: temperature, top-k and top-p (nucleus)
Changed parts are marked with  # NEW

Read top to bottom:  GPTConfig -> CausalSelfAttention -> MLP -> Block -> GPT
Shapes in comments: B = batch size, T = time (number of tokens), C = channels (n_embd),
                    nh = number of heads, hs = head size (C // nh), V = vocabulary size.
"""
from dataclasses import dataclass

import torch
from torch import nn
from torch.nn import functional as F


@dataclass
class GPTConfig:
    vocab_size: int = 65       # how many different tokens exist (65 characters in Shakespeare)
    block_size: int = 64       # context length: the most tokens the model can look back at
    n_layer: int = 4           # how many Blocks are stacked
    n_head: int = 4            # attention heads per Block
    n_embd: int = 128          # numbers used to describe each token (C)
    dropout: float = 0.0       # fraction of activations randomly zeroed during training (fights overfitting)


class CausalSelfAttention(nn.Module):
    """Tokens look at earlier tokens and collect information from them (lesson 13, fast version)."""

    def __init__(self, cfg: GPTConfig):
        super().__init__()
        assert cfg.n_embd % cfg.n_head == 0, "n_embd must be divisible by n_head"
        self.n_head = cfg.n_head
        self.c_attn = nn.Linear(cfg.n_embd, 3 * cfg.n_embd)        # q, k, v for all heads in one matrix
        self.c_proj = nn.Linear(cfg.n_embd, cfg.n_embd)            # mixes the heads' results
        self.attn_drop = nn.Dropout(cfg.dropout)
        self.resid_drop = nn.Dropout(cfg.dropout)
        mask = torch.tril(torch.ones(cfg.block_size, cfg.block_size, dtype=torch.bool))
        self.register_buffer("mask", mask.view(1, 1, cfg.block_size, cfg.block_size))

    def forward(self, x, cache=None, layer=0):
        B, T, C = x.shape                                          # with a cache, T is usually 1 (the new token)
        q, k, v = self.c_attn(x).split(C, dim=2)                   # 3 x (B, T, C)
        q = q.view(B, T, self.n_head, C // self.n_head).transpose(1, 2)   # (B, nh, T, hs)
        k = k.view(B, T, self.n_head, C // self.n_head).transpose(1, 2)
        v = v.view(B, T, self.n_head, C // self.n_head).transpose(1, 2)
        past = 0
        if cache is not None:                                      # NEW: glue the remembered keys/values in front
            past = cache.length(layer)
            k, v = cache.append(layer, k, v)                       # (B, nh, past + T, hs)
        att = (q @ k.transpose(-2, -1)) * (k.size(-1) ** -0.5)    # (B, nh, T, past + T)
        # NEW: query i sits at position past+i, so it may see keys 0 .. past+i
        att = att.masked_fill(~self.mask[:, :, past:past + T, :past + T], float("-inf"))
        att = self.attn_drop(F.softmax(att, dim=-1))
        y = att @ v                                                # (B, nh, T, hs)
        y = y.transpose(1, 2).contiguous().view(B, T, C)           # glue the heads back together
        return self.resid_drop(self.c_proj(y))


class MLP(nn.Module):
    """After tokens 'talk' (attention), each token 'thinks' on its own: a small 2-layer network."""

    def __init__(self, cfg: GPTConfig):
        super().__init__()
        self.c_fc = nn.Linear(cfg.n_embd, 4 * cfg.n_embd)          # widen 4x (the GPT recipe)
        self.c_proj = nn.Linear(4 * cfg.n_embd, cfg.n_embd)        # back to n_embd
        self.drop = nn.Dropout(cfg.dropout)

    def forward(self, x):
        return self.drop(self.c_proj(F.gelu(self.c_fc(x))))        # GELU: a smooth ReLU


class Block(nn.Module):
    """One transformer block: communicate (attention), then compute (MLP).
    Both are added onto x ('residual connection'), after LayerNorm ('pre-norm')."""

    def __init__(self, cfg: GPTConfig):
        super().__init__()
        self.ln_1 = nn.LayerNorm(cfg.n_embd)
        self.attn = CausalSelfAttention(cfg)
        self.ln_2 = nn.LayerNorm(cfg.n_embd)
        self.mlp = MLP(cfg)

    def forward(self, x, cache=None, layer=0):
        x = x + self.attn(self.ln_1(x), cache, layer)    # x + ... = residual: the original signal always gets through
        x = x + self.mlp(self.ln_2(x))
        return x


class KVCache:  # NEW
    """For every layer, the keys and values of all tokens seen so far: shape (B, nh, tokens, hs)."""

    def __init__(self, n_layer):
        self.k, self.v = [None] * n_layer, [None] * n_layer

    def length(self, layer=0):
        return 0 if self.k[layer] is None else self.k[layer].size(2)

    def append(self, layer, k, v):
        if self.k[layer] is not None:
            k = torch.cat([self.k[layer], k], dim=2)               # old tokens + new tokens along the time axis
            v = torch.cat([self.v[layer], v], dim=2)
        self.k[layer], self.v[layer] = k, v
        return k, v

    def megabytes(self):
        return sum(t.numel() * t.element_size() for t in self.k + self.v if t is not None) / 1e6


def filter_logits(logits, temperature=1.0, top_k=None, top_p=None):  # NEW
    """Shape the next-token scores (B, V) before sampling. Returns new scores; removed tokens get -inf."""
    logits = logits / max(temperature, 1e-8)                       # <1 sharpens, >1 flattens the distribution
    if top_k is not None:
        kth_best = torch.topk(logits, min(top_k, logits.size(-1))).values[:, [-1]]
        logits = logits.masked_fill(logits < kth_best, float("-inf"))   # keep only the k best tokens
    if top_p is not None:
        sorted_logits, sorted_idx = torch.sort(logits, descending=True)
        probs = F.softmax(sorted_logits, dim=-1)
        before = probs.cumsum(dim=-1) - probs                      # probability mass of the tokens ranked above
        remove_sorted = before > top_p                             # drop a token once the ones above already cover p
        remove = remove_sorted.scatter(1, sorted_idx, remove_sorted)   # back to the original token order
        logits = logits.masked_fill(remove, float("-inf"))
    return logits


class GPT(nn.Module):
    def __init__(self, cfg: GPTConfig):
        super().__init__()
        self.cfg = cfg
        self.wte = nn.Embedding(cfg.vocab_size, cfg.n_embd)        # token embedding: WHAT the token is
        self.wpe = nn.Embedding(cfg.block_size, cfg.n_embd)        # position embedding: WHERE it is
        self.drop = nn.Dropout(cfg.dropout)
        self.blocks = nn.ModuleList([Block(cfg) for _ in range(cfg.n_layer)])
        self.ln_f = nn.LayerNorm(cfg.n_embd)                       # final LayerNorm
        self.lm_head = nn.Linear(cfg.n_embd, cfg.vocab_size, bias=False)  # n_embd numbers -> one score per token
        self.apply(self._init_weights)

    def _init_weights(self, module):
        # Small random starting weights (std 0.02, like GPT-2) keep the first losses sensible.
        if isinstance(module, nn.Linear):
            nn.init.normal_(module.weight, mean=0.0, std=0.02)
            if module.bias is not None:
                nn.init.zeros_(module.bias)
        elif isinstance(module, nn.Embedding):
            nn.init.normal_(module.weight, mean=0.0, std=0.02)

    def num_params(self):
        return sum(p.numel() for p in self.parameters())

    def forward(self, idx, targets=None, cache=None):
        B, T = idx.shape
        past = cache.length() if cache is not None else 0          # NEW: tokens already in the cache
        assert past + T <= self.cfg.block_size, f"{past + T} tokens is longer than block_size {self.cfg.block_size}"
        pos = torch.arange(past, past + T, device=idx.device)      # NEW: positions continue after the cached ones
        x = self.drop(self.wte(idx) + self.wpe(pos))               # (B, T, C) + (T, C) -> (B, T, C)
        for i, block in enumerate(self.blocks):
            x = block(x, cache, i)
        logits = self.lm_head(self.ln_f(x))                        # (B, T, V): next-token scores at EVERY position
        loss = None
        if targets is not None:                                    # cross-entropy = -log(probability of the right answer)
            loss = F.cross_entropy(logits.view(B * T, -1), targets.view(B * T))
        return logits, loss

    @torch.no_grad()
    def generate(self, idx, max_new_tokens, temperature=1.0, top_k=None, top_p=None, greedy=False, use_cache=True):
        """Append max_new_tokens tokens to idx (B, T).
        greedy=True always takes the single most likely token. use_cache=False recomputes everything each step."""
        cache = KVCache(self.cfg.n_layer) if use_cache else None
        new = idx                                                  # what still has to go through the model
        for _ in range(max_new_tokens):
            if use_cache:
                if cache.length() + new.size(1) > self.cfg.block_size:
                    # The window is full (position embeddings stop at block_size): start a fresh cache
                    # from the last block_size tokens. Same result as no cache, but no speed-up from here on.
                    cache, new = KVCache(self.cfg.n_layer), idx[:, -self.cfg.block_size:]
                logits, _ = self(new, cache=cache)                 # first step: the whole prompt; then 1 token
            else:
                logits, _ = self(idx[:, -self.cfg.block_size:])    # every step: the whole text again
            logits = logits[:, -1, :]                              # scores for the next token: (B, V)
            if greedy:
                idx_next = logits.argmax(dim=-1, keepdim=True)
            else:
                probs = F.softmax(filter_logits(logits, temperature, top_k, top_p), dim=-1)
                idx_next = torch.multinomial(probs, num_samples=1)
            idx = torch.cat((idx, idx_next), dim=1)
            new = idx_next
        return idx
