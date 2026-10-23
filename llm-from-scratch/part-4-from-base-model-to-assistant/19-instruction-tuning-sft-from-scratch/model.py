"""The LLaMA-style GPT from lesson 17 (unchanged copy), used by the chat lessons 19-22. The four switches:

    norm   = "layernorm" (GPT-2)      or "rmsnorm" (LLaMA)
    pos    = "learned"   (GPT-2)      or "rope"    (LLaMA: rotary position embeddings)
    mlp    = "gelu"      (GPT-2)      or "swiglu"  (LLaMA)
    n_kv_head = n_head   (GPT-2)      or fewer     (LLaMA 2/3: grouped-query attention, GQA)

Read top to bottom: Config -> RMSNorm -> RoPE helpers -> Attention -> MLPs -> Block -> GPT.
Shapes: B batch, T tokens, C n_embd, nh query heads, nkv key/value heads, hs head size.
"""
from dataclasses import dataclass

import torch
from torch import nn
from torch.nn import functional as F


@dataclass
class Config:
    vocab_size: int = 65
    block_size: int = 64
    n_layer: int = 4
    n_head: int = 4
    n_kv_head: int = 4          # = n_head: normal multi-head attention; smaller: GQA; 1: multi-query attention
    n_embd: int = 128
    norm: str = "layernorm"
    pos: str = "learned"
    mlp: str = "gelu"
    bias: bool = True           # LLaMA drops the bias vectors from all Linear layers
    rope_theta: float = 10000.0  # RoPE's base: sets how fast the rotation angles change


GPT2_STYLE = dict(norm="layernorm", pos="learned", mlp="gelu", bias=True)
LLAMA_STYLE = dict(norm="rmsnorm", pos="rope", mlp="swiglu", bias=False, n_kv_head=2)


# ----------------------------------------------------------------------------- RMSNorm
class RMSNorm(nn.Module):
    """LayerNorm without the 'subtract the mean' part and without a bias:
    divide each token's vector by its root-mean-square (its typical size), then scale by a learned weight."""

    def __init__(self, dim, eps=1e-6):
        super().__init__()
        self.eps = eps                                   # tiny number so we never divide by zero
        self.weight = nn.Parameter(torch.ones(dim))

    def forward(self, x):
        rms = torch.sqrt(x.pow(2).mean(dim=-1, keepdim=True) + self.eps)
        return x / rms * self.weight


def make_norm(cfg):
    return RMSNorm(cfg.n_embd) if cfg.norm == "rmsnorm" else nn.LayerNorm(cfg.n_embd, bias=cfg.bias)


# ----------------------------------------------------------------------------- RoPE
def rope_cos_sin(T, hs, theta=10000.0, device=None):
    """Angles for every (position, pair of numbers). Pair i turns at speed theta^(-2i/hs) per position:
    the first pairs spin fast (good for nearby tokens), the last ones slowly (good for far-away tokens)."""
    inv_freq = 1.0 / (theta ** (torch.arange(0, hs, 2, device=device).float() / hs))   # (hs/2,)
    angles = torch.arange(T, device=device).float()[:, None] * inv_freq[None, :]      # (T, hs/2)
    return angles.cos(), angles.sin()


def apply_rope(x, cos, sin):
    """Rotate each pair (x1, x2) of a query/key by its position's angle. x: (B, heads, T, hs)."""
    half = x.size(-1) // 2
    x1, x2 = x[..., :half], x[..., half:]               # pair number i = (x1[i], x2[i])
    # 2-D rotation: (x1, x2) -> (x1 cos a - x2 sin a, x1 sin a + x2 cos a)
    return torch.cat([x1 * cos - x2 * sin, x1 * sin + x2 * cos], dim=-1)


# ----------------------------------------------------------------------------- attention (with GQA)
class Attention(nn.Module):
    def __init__(self, cfg):
        super().__init__()
        assert cfg.n_embd % cfg.n_head == 0 and cfg.n_head % cfg.n_kv_head == 0
        self.nh, self.nkv, self.hs = cfg.n_head, cfg.n_kv_head, cfg.n_embd // cfg.n_head
        self.cfg = cfg
        self.q_proj = nn.Linear(cfg.n_embd, self.nh * self.hs, bias=cfg.bias)
        self.k_proj = nn.Linear(cfg.n_embd, self.nkv * self.hs, bias=cfg.bias)   # fewer key heads with GQA...
        self.v_proj = nn.Linear(cfg.n_embd, self.nkv * self.hs, bias=cfg.bias)   # ...and fewer value heads
        self.o_proj = nn.Linear(cfg.n_embd, cfg.n_embd, bias=cfg.bias)

    def forward(self, x):
        B, T, C = x.shape
        q = self.q_proj(x).view(B, T, self.nh, self.hs).transpose(1, 2)     # (B, nh, T, hs)
        k = self.k_proj(x).view(B, T, self.nkv, self.hs).transpose(1, 2)    # (B, nkv, T, hs)
        v = self.v_proj(x).view(B, T, self.nkv, self.hs).transpose(1, 2)
        if self.cfg.pos == "rope":                       # position goes INTO q and k by rotating them
            cos, sin = rope_cos_sin(T, self.hs, self.cfg.rope_theta, x.device)
            q, k = apply_rope(q, cos, sin), apply_rope(k, cos, sin)
        if self.nkv != self.nh:                          # GQA: each key/value head is shared by a group of query heads
            k = k.repeat_interleave(self.nh // self.nkv, dim=1)              # (B, nh, T, hs)
            v = v.repeat_interleave(self.nh // self.nkv, dim=1)
        y = F.scaled_dot_product_attention(q, k, v, is_causal=True)          # lesson 13's maths, fused
        return self.o_proj(y.transpose(1, 2).contiguous().view(B, T, C))


# ----------------------------------------------------------------------------- MLPs
class GeluMLP(nn.Module):
    def __init__(self, cfg):
        super().__init__()
        self.up = nn.Linear(cfg.n_embd, 4 * cfg.n_embd, bias=cfg.bias)
        self.down = nn.Linear(4 * cfg.n_embd, cfg.n_embd, bias=cfg.bias)

    def forward(self, x):
        return self.down(F.gelu(self.up(x)))


class SwiGLU(nn.Module):
    """Two parallel 'up' layers: one goes through SiLU and acts as a GATE (how much to let through),
    the other carries the content; multiply them, then project down.
    Hidden size 2/3 * 4 * n_embd keeps the parameter count about equal to the GELU MLP (3 matrices instead of 2)."""

    def __init__(self, cfg):
        super().__init__()
        hidden = int(2 * 4 * cfg.n_embd / 3)
        hidden = 16 * ((hidden + 15) // 16)              # round up to a multiple of 16 (hardware likes it)
        self.gate = nn.Linear(cfg.n_embd, hidden, bias=cfg.bias)
        self.up = nn.Linear(cfg.n_embd, hidden, bias=cfg.bias)
        self.down = nn.Linear(hidden, cfg.n_embd, bias=cfg.bias)

    def forward(self, x):
        return self.down(F.silu(self.gate(x)) * self.up(x))   # silu(z) = z * sigmoid(z)


# ----------------------------------------------------------------------------- block + model
class Block(nn.Module):
    def __init__(self, cfg):
        super().__init__()
        self.norm1, self.attn = make_norm(cfg), Attention(cfg)
        self.norm2 = make_norm(cfg)
        self.mlp = SwiGLU(cfg) if cfg.mlp == "swiglu" else GeluMLP(cfg)

    def forward(self, x):
        x = x + self.attn(self.norm1(x))
        x = x + self.mlp(self.norm2(x))
        return x


class GPT(nn.Module):
    def __init__(self, cfg):
        super().__init__()
        self.cfg = cfg
        self.wte = nn.Embedding(cfg.vocab_size, cfg.n_embd)
        self.wpe = nn.Embedding(cfg.block_size, cfg.n_embd) if cfg.pos == "learned" else None   # RoPE needs no table
        self.blocks = nn.ModuleList([Block(cfg) for _ in range(cfg.n_layer)])
        self.norm_f = make_norm(cfg)
        self.lm_head = nn.Linear(cfg.n_embd, cfg.vocab_size, bias=False)
        for m in self.modules():                         # GPT-2 style small random start
            if isinstance(m, (nn.Linear, nn.Embedding)):
                nn.init.normal_(m.weight, mean=0.0, std=0.02)
            if isinstance(m, nn.Linear) and m.bias is not None:
                nn.init.zeros_(m.bias)

    def num_params(self):
        return sum(p.numel() for p in self.parameters())

    def forward(self, idx, targets=None):
        B, T = idx.shape
        x = self.wte(idx)
        if self.wpe is not None:
            x = x + self.wpe(torch.arange(T, device=idx.device))
        for block in self.blocks:
            x = block(x)
        logits = self.lm_head(self.norm_f(x))
        loss = None if targets is None else F.cross_entropy(logits.view(B * T, -1), targets.reshape(B * T), ignore_index=-100)
        return logits, loss

    @torch.no_grad()
    def generate(self, idx, max_new_tokens, temperature=0.8, top_k=None, stop_id=None):
        for _ in range(max_new_tokens):
            logits, _ = self(idx[:, -self.cfg.block_size:])
            logits = logits[:, -1, :] / temperature
            if top_k is not None:
                v, _ = torch.topk(logits, min(top_k, logits.size(-1)))
                logits[logits < v[:, [-1]]] = float("-inf")
            nxt = torch.multinomial(F.softmax(logits, dim=-1), 1)
            idx = torch.cat((idx, nxt), dim=1)
            if stop_id is not None and (nxt == stop_id).all():   # used by the chat lessons: stop at <|end|>
                break
        return idx
