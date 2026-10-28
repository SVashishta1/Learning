"""GPT-2, exactly as OpenAI built it, in one file (in the style of Karpathy's build-nanogpt).

Differences from lesson 14's character GPT are small but important:
  * parameter NAMES match OpenAI/Hugging Face (transformer.h.0.attn.c_attn ...) so real GPT-2 weights load
  * GELU uses the 'tanh' approximation (what GPT-2 used in 2019)
  * the token embedding and the output layer SHARE one matrix ("weight tying")
  * residual projections start smaller (std scaled by 1/sqrt(2 * n_layer))
  * attention uses PyTorch's fused F.scaled_dot_product_attention (FlashAttention on GPUs)
"""
import inspect
import math
from dataclasses import dataclass

import torch
from torch import nn
from torch.nn import functional as F


@dataclass
class GPTConfig:
    block_size: int = 1024     # GPT-2 reads up to 1,024 tokens
    vocab_size: int = 50257    # 50,000 BPE merges + 256 bytes + 1 special token <|endoftext|>
    n_layer: int = 12
    n_head: int = 12
    n_embd: int = 768


class CausalSelfAttention(nn.Module):
    def __init__(self, cfg):
        super().__init__()
        assert cfg.n_embd % cfg.n_head == 0
        self.c_attn = nn.Linear(cfg.n_embd, 3 * cfg.n_embd)
        self.c_proj = nn.Linear(cfg.n_embd, cfg.n_embd)
        self.c_proj.SCALE_INIT = True          # marks a layer that writes into the residual stream
        self.n_head, self.n_embd = cfg.n_head, cfg.n_embd

    def forward(self, x):
        B, T, C = x.size()
        q, k, v = self.c_attn(x).split(self.n_embd, dim=2)
        q, k, v = (t.view(B, T, self.n_head, C // self.n_head).transpose(1, 2) for t in (q, k, v))  # (B, nh, T, hs)
        # Same maths as lesson 13 (scores, mask, softmax, @ v), but fused into one fast kernel
        # that never builds the full (T, T) matrix in slow memory: "FlashAttention".
        y = F.scaled_dot_product_attention(q, k, v, is_causal=True)
        y = y.transpose(1, 2).contiguous().view(B, T, C)
        return self.c_proj(y)


class MLP(nn.Module):
    def __init__(self, cfg):
        super().__init__()
        self.c_fc = nn.Linear(cfg.n_embd, 4 * cfg.n_embd)
        self.gelu = nn.GELU(approximate="tanh")
        self.c_proj = nn.Linear(4 * cfg.n_embd, cfg.n_embd)
        self.c_proj.SCALE_INIT = True

    def forward(self, x):
        return self.c_proj(self.gelu(self.c_fc(x)))


class Block(nn.Module):
    def __init__(self, cfg):
        super().__init__()
        self.ln_1 = nn.LayerNorm(cfg.n_embd)
        self.attn = CausalSelfAttention(cfg)
        self.ln_2 = nn.LayerNorm(cfg.n_embd)
        self.mlp = MLP(cfg)

    def forward(self, x):
        x = x + self.attn(self.ln_1(x))
        x = x + self.mlp(self.ln_2(x))
        return x


class GPT(nn.Module):
    def __init__(self, cfg):
        super().__init__()
        self.config = cfg
        self.transformer = nn.ModuleDict(dict(
            wte=nn.Embedding(cfg.vocab_size, cfg.n_embd),
            wpe=nn.Embedding(cfg.block_size, cfg.n_embd),
            h=nn.ModuleList([Block(cfg) for _ in range(cfg.n_layer)]),
            ln_f=nn.LayerNorm(cfg.n_embd),
        ))
        self.lm_head = nn.Linear(cfg.n_embd, cfg.vocab_size, bias=False)
        # Weight tying: reading a token (wte) and writing a token (lm_head) use the same table.
        # Saves 38.6M of GPT-2's 163M parameters and works slightly better.
        self.transformer.wte.weight = self.lm_head.weight
        self.apply(self._init_weights)

    def _init_weights(self, module):
        if isinstance(module, nn.Linear):
            std = 0.02
            if getattr(module, "SCALE_INIT", False):
                # 2 residual additions per block: scale down so the residual stream doesn't grow with depth
                std *= (2 * self.config.n_layer) ** -0.5
            nn.init.normal_(module.weight, mean=0.0, std=std)
            if module.bias is not None:
                nn.init.zeros_(module.bias)
        elif isinstance(module, nn.Embedding):
            nn.init.normal_(module.weight, mean=0.0, std=0.02)

    def forward(self, idx, targets=None):
        B, T = idx.size()
        assert T <= self.config.block_size, f"sequence length {T} > block_size {self.config.block_size}"
        pos = torch.arange(0, T, dtype=torch.long, device=idx.device)
        x = self.transformer.wte(idx) + self.transformer.wpe(pos)
        for block in self.transformer.h:
            x = block(x)
        logits = self.lm_head(self.transformer.ln_f(x))
        loss = None
        if targets is not None:
            loss = F.cross_entropy(logits.view(-1, logits.size(-1)).float(), targets.view(-1))
        return logits, loss

    # ------------------------------------------------------------------ loading OpenAI's weights
    @classmethod
    def from_hf_model(cls, model_hf):
        """Copy the weights of a Hugging Face GPT2LMHeadModel into our GPT."""
        c = model_hf.config
        model = cls(GPTConfig(block_size=c.n_positions, vocab_size=c.vocab_size,
                              n_layer=c.n_layer, n_head=c.n_head, n_embd=c.n_embd))
        sd, sd_hf = model.state_dict(), model_hf.state_dict()
        keys_hf = [k for k in sd_hf if not k.endswith((".attn.masked_bias", ".attn.bias"))]  # buffers, not weights
        assert len(keys_hf) == len(sd), f"mismatched keys: {len(keys_hf)} != {len(sd)}"
        # OpenAI's code used a 'Conv1D' layer that stores these 4 matrices transposed (in, out)
        # instead of nn.Linear's (out, in). We flip them while copying.
        transposed = ["attn.c_attn.weight", "attn.c_proj.weight", "mlp.c_fc.weight", "mlp.c_proj.weight"]
        with torch.no_grad():
            for k in keys_hf:
                if any(k.endswith(w) for w in transposed):
                    assert sd_hf[k].shape[::-1] == sd[k].shape
                    sd[k].copy_(sd_hf[k].t())
                else:
                    assert sd_hf[k].shape == sd[k].shape, k
                    sd[k].copy_(sd_hf[k])
        return model

    @classmethod
    def from_pretrained(cls, model_type="gpt2"):
        """Download OpenAI's GPT-2 from the Hugging Face Hub (needs `pip install transformers` + internet)."""
        assert model_type in {"gpt2", "gpt2-medium", "gpt2-large", "gpt2-xl"}
        from transformers import GPT2LMHeadModel
        print(f"loading weights of pretrained {model_type} ...")
        return cls.from_hf_model(GPT2LMHeadModel.from_pretrained(model_type))

    # ------------------------------------------------------------------ the optimizer
    def configure_optimizers(self, weight_decay, learning_rate, device_type, verbose=True):
        """AdamW with weight decay only on 2-D weights (matrices, embeddings), not on biases/LayerNorms."""
        params = [p for p in self.parameters() if p.requires_grad]
        decay = [p for p in params if p.dim() >= 2]
        no_decay = [p for p in params if p.dim() < 2]
        groups = [{"params": decay, "weight_decay": weight_decay}, {"params": no_decay, "weight_decay": 0.0}]
        fused = "fused" in inspect.signature(torch.optim.AdamW).parameters and device_type == "cuda"
        if verbose:
            print(f"decayed: {sum(p.numel() for p in decay):,} params | not decayed: "
                  f"{sum(p.numel() for p in no_decay):,} params | fused AdamW: {fused}")
        return torch.optim.AdamW(groups, lr=learning_rate, betas=(0.9, 0.95), eps=1e-8, fused=fused)

    @torch.no_grad()
    def generate(self, idx, max_new_tokens, top_k=50, temperature=1.0):
        for _ in range(max_new_tokens):
            logits, _ = self(idx[:, -self.config.block_size:])
            logits = logits[:, -1, :].float() / temperature
            v, ix = torch.topk(logits, top_k, dim=-1)              # keep the 50 best (Hugging Face default)
            choice = torch.multinomial(F.softmax(v, dim=-1), 1)
            idx = torch.cat((idx, torch.gather(ix, -1, choice)), dim=1)
        return idx


def cosine_lr(step, max_lr, warmup_steps, max_steps, min_ratio=0.1):
    """Learning-rate schedule: straight line up for `warmup_steps`, then a cosine curve down to 10%."""
    min_lr = max_lr * min_ratio
    if step < warmup_steps:
        return max_lr * (step + 1) / warmup_steps
    if step >= max_steps:
        return min_lr
    ratio = (step - warmup_steps) / (max_steps - warmup_steps)     # 0 -> 1
    coeff = 0.5 * (1.0 + math.cos(math.pi * ratio))                # 1 -> 0, smoothly
    return min_lr + coeff * (max_lr - min_lr)
