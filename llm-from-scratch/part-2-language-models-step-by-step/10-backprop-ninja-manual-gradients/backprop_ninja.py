"""Lesson 10: become a backprop ninja. Write EVERY gradient of the MLP + BatchNorm model by hand,
then check each one against PyTorch's loss.backward().

Exercise 1: backprop through the forward pass broken into ~20 tiny steps ("atomic" ops).
Exercise 2: the shortcut for softmax + cross-entropy: dlogits = (probs - one_hot) / n.
Exercise 3: the shortcut for the whole BatchNorm layer in one formula.
(Exercise 4, training with only our own gradients, is in train_manual.py.)

Usage:  python backprop_ninja.py   (a few seconds)
"""
import torch
import torch.nn.functional as F

torch.set_num_threads(1)   # tiny matrices: one CPU thread is fastest

N_EMBD, N_HIDDEN, BLOCK_SIZE, VOCAB = 10, 64, 3, 27


def make_params(seed=2147483647):
    g = torch.Generator().manual_seed(seed)
    C = torch.randn((VOCAB, N_EMBD), generator=g)
    fan_in = N_EMBD * BLOCK_SIZE
    W1 = torch.randn((fan_in, N_HIDDEN), generator=g) * (5 / 3) / fan_in**0.5   # Kaiming init for tanh
    b1 = torch.randn(N_HIDDEN, generator=g) * 0.1      # useless with BatchNorm, but kept so we practise its grad
    W2 = torch.randn((N_HIDDEN, VOCAB), generator=g) * 0.1
    b2 = torch.randn(VOCAB, generator=g) * 0.1
    bngain = torch.randn((1, N_HIDDEN), generator=g) * 0.1 + 1.0   # not exactly 1 and 0, so no bug can hide
    bnbias = torch.randn((1, N_HIDDEN), generator=g) * 0.1
    params = {"C": C, "W1": W1, "b1": b1, "W2": W2, "b2": b2, "bngain": bngain, "bnbias": bnbias}
    for p in params.values():
        p.requires_grad = True
    return params


def forward_atomic(P, Xb, Yb):
    """The forward pass split into small steps, so each step's backward is easy. Returns every piece."""
    n = Xb.shape[0]
    t = {}
    t["emb"] = P["C"][Xb]                                          # (n, 3, 10) embeddings
    t["embcat"] = t["emb"].view(n, -1)                             # (n, 30) joined
    t["hprebn"] = t["embcat"] @ P["W1"] + P["b1"]                  # (n, 64) hidden layer before BatchNorm
    t["bnmeani"] = 1 / n * t["hprebn"].sum(0, keepdim=True)        # (1, 64) mean of each neuron over the batch
    t["bndiff"] = t["hprebn"] - t["bnmeani"]                       # (n, 64) distance from the mean
    t["bndiff2"] = t["bndiff"] ** 2
    t["bnvar"] = 1 / (n - 1) * t["bndiff2"].sum(0, keepdim=True)   # (1, 64) variance (Bessel's n-1, see README)
    t["bnvar_inv"] = (t["bnvar"] + 1e-5) ** -0.5                   # 1 / standard deviation
    t["bnraw"] = t["bndiff"] * t["bnvar_inv"]                      # (n, 64) normalised: mean 0, std 1
    t["hpreact"] = P["bngain"] * t["bnraw"] + P["bnbias"]          # scale and shift
    t["h"] = torch.tanh(t["hpreact"])                              # (n, 64) hidden activations
    t["logits"] = t["h"] @ P["W2"] + P["b2"]                       # (n, 27)
    t["logit_maxes"] = t["logits"].max(1, keepdim=True).values     # (n, 1) for numerical safety
    t["norm_logits"] = t["logits"] - t["logit_maxes"]
    t["counts"] = t["norm_logits"].exp()
    t["counts_sum"] = t["counts"].sum(1, keepdim=True)             # (n, 1)
    t["counts_sum_inv"] = t["counts_sum"] ** -1
    t["probs"] = t["counts"] * t["counts_sum_inv"]                 # (n, 27) softmax probabilities
    t["logprobs"] = t["probs"].log()
    t["loss"] = -t["logprobs"][torch.arange(n), Yb].mean()
    return t


def manual_backward(P, t, Xb, Yb):
    """Exercise 1: walk backwards through forward_atomic, one chain-rule step per line."""
    n = Xb.shape[0]
    d = {}
    # loss = -(mean of the n picked logprobs): each picked one gets -1/n, all others 0
    d["logprobs"] = torch.zeros_like(t["logprobs"])
    d["logprobs"][torch.arange(n), Yb] = -1.0 / n
    d["probs"] = (1.0 / t["probs"]) * d["logprobs"]                                  # d log(x) = 1/x
    d["counts_sum_inv"] = (t["counts"] * d["probs"]).sum(1, keepdim=True)            # broadcast forward -> sum backward
    d["counts"] = t["counts_sum_inv"] * d["probs"]                                   # first use of counts
    d["counts_sum"] = (-t["counts_sum"] ** -2) * d["counts_sum_inv"]                 # d x^-1 = -x^-2
    d["counts"] = d["counts"] + torch.ones_like(t["counts"]) * d["counts_sum"]       # second use (the sum): add!
    d["norm_logits"] = t["counts"] * d["counts"]                                     # d e^x = e^x
    d["logit_maxes"] = (-d["norm_logits"]).sum(1, keepdim=True)
    d["logits"] = d["norm_logits"].clone()
    d["logits"] += F.one_hot(t["logits"].max(1).indices, num_classes=VOCAB) * d["logit_maxes"]  # max: only the winner gets grad
    d["h"] = d["logits"] @ P["W2"].T
    d["W2"] = t["h"].T @ d["logits"]
    d["b2"] = d["logits"].sum(0)
    d["hpreact"] = (1.0 - t["h"] ** 2) * d["h"]                                      # d tanh = 1 - tanh^2
    d["bngain"] = (t["bnraw"] * d["hpreact"]).sum(0, keepdim=True)
    d["bnraw"] = P["bngain"] * d["hpreact"]
    d["bnbias"] = d["hpreact"].sum(0, keepdim=True)
    d["bndiff"] = t["bnvar_inv"] * d["bnraw"]                                        # first use of bndiff
    d["bnvar_inv"] = (t["bndiff"] * d["bnraw"]).sum(0, keepdim=True)
    d["bnvar"] = (-0.5 * (t["bnvar"] + 1e-5) ** -1.5) * d["bnvar_inv"]
    d["bndiff2"] = (1.0 / (n - 1)) * torch.ones_like(t["bndiff2"]) * d["bnvar"]
    d["bndiff"] = d["bndiff"] + (2 * t["bndiff"]) * d["bndiff2"]                     # second use: add!
    d["hprebn"] = d["bndiff"].clone()
    d["bnmeani"] = (-d["bndiff"]).sum(0, keepdim=True)
    d["hprebn"] += 1.0 / n * torch.ones_like(t["hprebn"]) * d["bnmeani"]            # the mean used every row
    d["embcat"] = d["hprebn"] @ P["W1"].T
    d["W1"] = t["embcat"].T @ d["hprebn"]
    d["b1"] = d["hprebn"].sum(0)
    d["emb"] = d["embcat"].view(t["emb"].shape)                                      # undo the view
    d["C"] = torch.zeros_like(P["C"])
    d["C"].index_add_(0, Xb.view(-1), d["emb"].view(-1, N_EMBD))                     # each lookup sends grad back to its row
    return d


def fast_dlogits(logits, Yb):
    """Exercise 2: the whole softmax + cross-entropy backward in three lines."""
    n = logits.shape[0]
    dlogits = F.softmax(logits, 1)
    dlogits[torch.arange(n), Yb] -= 1          # probs - one_hot(Y)
    return dlogits / n                         # / n because the loss is a mean


def fast_dhprebn(bngain, bnvar_inv, bnraw, dhpreact):
    """Exercise 3: the whole BatchNorm backward (from dhpreact to dhprebn) in one formula."""
    n = dhpreact.shape[0]
    return bngain * bnvar_inv / n * (n * dhpreact - dhpreact.sum(0) - n / (n - 1) * bnraw * (dhpreact * bnraw).sum(0))


def cmp(name, ours, torch_grad):
    exact = torch.all(ours == torch_grad).item()
    approx = torch.allclose(ours, torch_grad)
    maxdiff = (ours - torch_grad).abs().max().item()
    print(f"{name:15s} | exact: {str(exact):5s} | approximate: {str(approx):5s} | maxdiff: {maxdiff:.1e}")
    return approx


def run_all(Xb, Yb, verbose=True):
    """Run all three exercises on one batch. Returns True if every gradient matches PyTorch."""
    say = print if verbose else (lambda *a, **k: None)
    P = make_params()
    t = forward_atomic(P, Xb, Yb)
    for v in t.values():
        v.retain_grad()                        # ask PyTorch to keep the grads of intermediate tensors too
    t["loss"].backward()
    d = manual_backward(P, t, Xb, Yb)
    check = cmp if verbose else (lambda name, a, b: torch.allclose(a, b))

    say(f"loss = {t['loss'].item():.6f}\n\nEXERCISE 1: every intermediate, ours vs PyTorch")
    ok = True
    order = ["logprobs", "probs", "counts_sum_inv", "counts_sum", "counts", "norm_logits", "logit_maxes",
             "logits", "h", "W2", "b2", "hpreact", "bngain", "bnbias", "bnraw", "bnvar_inv", "bnvar",
             "bndiff2", "bndiff", "bnmeani", "hprebn", "embcat", "W1", "b1", "emb", "C"]
    for name in order:
        torch_grad = P[name].grad if name in P else t[name].grad
        ok &= check(name, d[name], torch_grad)

    say("\nEXERCISE 2: softmax + cross-entropy in one step")
    loss_fast = F.cross_entropy(t["logits"].detach(), Yb)
    say(f"F.cross_entropy loss {loss_fast.item():.6f}  vs atomic loss {t['loss'].item():.6f}"
        f"  diff {(loss_fast - t['loss']).abs().item():.1e}")
    ok &= check("logits (fast)", fast_dlogits(t["logits"].detach(), Yb), t["logits"].grad)

    say("\nEXERCISE 3: BatchNorm backward in one formula")
    ok &= check("hprebn (fast)", fast_dhprebn(P["bngain"].detach(), t["bnvar_inv"].detach(),
                                               t["bnraw"].detach(), t["hpreact"].grad), t["hprebn"].grad)
    return ok


if __name__ == "__main__":
    from names_data import load_words

    words = load_words()
    chars = sorted(set("".join(words)))
    stoi = {s: i + 1 for i, s in enumerate(chars)}
    stoi["."] = 0
    X, Y = [], []
    for w in words[:2000]:                     # a small slice is plenty for one batch
        context = [0] * BLOCK_SIZE
        for ch in w + ".":
            X.append(context)
            Y.append(stoi[ch])
            context = context[1:] + [stoi[ch]]
    X, Y = torch.tensor(X), torch.tensor(Y)
    g = torch.Generator().manual_seed(42)
    ix = torch.randint(0, X.shape[0], (32,), generator=g)  # one batch of 32 examples
    ok = run_all(X[ix], Y[ix])
    print("\nALL GRADIENTS MATCH. You are a backprop ninja." if ok else "\nSome gradients differ: look for 'False' above.")
