"""Tests for gpt2.py. Run with:  pytest -q

The key test builds a SMALL randomly-initialised Hugging Face GPT-2 on your machine (no download),
copies its weights into our GPT with from_hf_model(), and checks both give the same outputs.
If that passes, loading the real 124M GPT-2 works the same way.
"""
import math

import pytest
import torch

from gpt2 import GPT, GPTConfig, cosine_lr


def test_shapes_and_initial_loss():
    torch.manual_seed(0)
    cfg = GPTConfig(block_size=32, vocab_size=100, n_layer=2, n_head=2, n_embd=32)
    model = GPT(cfg)
    idx, targets = torch.randint(100, (3, 16)), torch.randint(100, (3, 16))
    logits, loss = model(idx, targets)
    assert logits.shape == (3, 16, 100)
    assert abs(loss.item() - math.log(100)) < 0.1          # a fresh model guesses evenly: loss ~ ln(vocab)
    assert model.lm_head.weight is model.transformer.wte.weight   # weight tying


def test_cosine_schedule():
    assert cosine_lr(0, 1.0, 10, 100) == pytest.approx(0.1)        # warm-up starts low
    assert cosine_lr(9, 1.0, 10, 100) == pytest.approx(1.0)        # ...and reaches the max
    assert cosine_lr(55, 1.0, 10, 100) == pytest.approx(0.55)      # half-way down the cosine: (1 + 0.1) / 2
    assert cosine_lr(100, 1.0, 10, 100) == pytest.approx(0.1)      # ends at 10%


def test_matches_huggingface_gpt2():
    transformers = pytest.importorskip("transformers")
    torch.manual_seed(0)
    hf_cfg = transformers.GPT2Config(n_positions=64, n_embd=48, n_layer=2, n_head=4, vocab_size=300,
                                     activation_function="gelu_new", resid_pdrop=0.0, embd_pdrop=0.0, attn_pdrop=0.0)
    hf = transformers.GPT2LMHeadModel(hf_cfg).eval()     # random weights, built locally
    ours = GPT.from_hf_model(hf).eval()
    idx = torch.randint(300, (2, 20))
    with torch.no_grad():
        diff = (hf(idx).logits - ours(idx)[0]).abs().max().item()
    assert diff < 1e-4, diff
