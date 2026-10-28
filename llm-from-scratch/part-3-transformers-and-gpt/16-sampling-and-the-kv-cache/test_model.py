"""Tests for model.py. Run with:  pytest -q"""
import torch

from model import GPT, GPTConfig, KVCache, filter_logits


def test_cache_gives_same_logits_as_full_forward():
    torch.manual_seed(0)
    model = GPT(GPTConfig(vocab_size=20, block_size=16, n_layer=2, n_head=2, n_embd=32)).eval()
    idx = torch.randint(20, (2, 12))
    with torch.no_grad():
        full, _ = model(idx)                                  # all 12 positions at once
        cache = KVCache(2)
        first, _ = model(idx[:, :5], cache=cache)             # a 5-token "prompt"...
        steps = [model(idx[:, t:t + 1], cache=cache)[0] for t in range(5, 12)]   # ...then one token at a time
    incremental = torch.cat([first] + steps, dim=1)
    assert torch.allclose(full, incremental, atol=1e-5)
    assert cache.length() == 12


def test_filters():
    logits = torch.log(torch.tensor([[0.5, 0.3, 0.15, 0.05]]))
    probs = lambda lg: torch.softmax(lg, dim=-1)[0]
    assert (probs(filter_logits(logits, top_k=2)) > 0).tolist() == [True, True, False, False]
    assert (probs(filter_logits(logits, top_p=0.75)) > 0).tolist() == [True, True, False, False]   # 0.5+0.3 >= 0.75
    assert (probs(filter_logits(logits, top_p=0.9)) > 0).tolist() == [True, True, True, False]
    assert (probs(filter_logits(logits, top_p=0.01)) > 0).tolist() == [True, False, False, False]  # always keep the best
    assert probs(filter_logits(logits, temperature=0.1))[0] > 0.99                                # cold = nearly greedy
