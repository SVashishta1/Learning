"""A GPT (decoder-only transformer) built from scratch: the whole model in one file.

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

    def forward(self, x):
        B, T, C = x.shape
        q, k, v = self.c_attn(x).split(C, dim=2)                   # 3 x (B, T, C)
        q = q.view(B, T, self.n_head, C // self.n_head).transpose(1, 2)   # (B, nh, T, hs)
        k = k.view(B, T, self.n_head, C // self.n_head).transpose(1, 2)
        v = v.view(B, T, self.n_head, C // self.n_head).transpose(1, 2)
        att = (q @ k.transpose(-2, -1)) * (k.size(-1) ** -0.5)    # (B, nh, T, T): who matches whom
        att = att.masked_fill(~self.mask[:, :, :T, :T], float("-inf"))  # no peeking at the future
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

    def forward(self, x):
        x = x + self.attn(self.ln_1(x))    # x + ... = residual: the original signal always gets through
        x = x + self.mlp(self.ln_2(x))
        return x


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

    def forward(self, idx, targets=None):
        B, T = idx.shape
        assert T <= self.cfg.block_size, f"sequence of {T} tokens is longer than block_size {self.cfg.block_size}"
        pos = torch.arange(T, device=idx.device)                   # 0, 1, 2, ..., T-1
        x = self.drop(self.wte(idx) + self.wpe(pos))               # (B, T, C) + (T, C) -> (B, T, C)
        for block in self.blocks:
            x = block(x)
        logits = self.lm_head(self.ln_f(x))                        # (B, T, V): next-token scores at EVERY position
        loss = None
        if targets is not None:                                    # cross-entropy = -log(probability of the right answer)
            loss = F.cross_entropy(logits.view(B * T, -1), targets.view(B * T))
        return logits, loss

    @torch.no_grad()
    def generate(self, idx, max_new_tokens, temperature=1.0, top_k=None):
        """Append one sampled token at a time. idx: (B, T) tensor of token ids to continue."""
        for _ in range(max_new_tokens):
            idx_cond = idx[:, -self.cfg.block_size:]               # the model can only see block_size tokens
            logits, _ = self(idx_cond)
            logits = logits[:, -1, :] / temperature               # scores for the NEXT token only: (B, V)
            if top_k is not None:
                v, _ = torch.topk(logits, min(top_k, logits.size(-1)))
                logits[logits < v[:, [-1]]] = float("-inf")       # keep only the k best candidates
            probs = F.softmax(logits, dim=-1)                      # scores -> probabilities
            idx_next = torch.multinomial(probs, num_samples=1)     # roll a weighted die: (B, 1)
            idx = torch.cat((idx, idx_next), dim=1)                # (B, T+1)
        return idx
