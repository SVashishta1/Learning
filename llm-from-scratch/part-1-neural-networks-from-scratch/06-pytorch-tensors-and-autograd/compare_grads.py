"""Lesson 06, part 2: prove that PyTorch's autograd computes the SAME gradients as our
hand-written numpy backward pass from lesson 05.

Same weights, same batch of real MNIST digits -> compare every gradient number.
"""
import numpy as np
import torch
import torch.nn.functional as F

from mnist import load_mnist


def numpy_loss_and_grads(W1, b1, W2, b2, X, y):
    """Lesson 05's forward + backward, written compactly (same maths, line for line)."""
    B = X.shape[0]
    z1 = X @ W1 + b1
    h = np.maximum(z1, 0)
    logits = h @ W2 + b2
    exps = np.exp(logits - logits.max(axis=1, keepdims=True))
    probs = exps / exps.sum(axis=1, keepdims=True)
    loss = -np.log(probs[np.arange(B), y]).mean()
    dlogits = probs.copy()
    dlogits[np.arange(B), y] -= 1
    dlogits /= B
    dh = dlogits @ W2.T
    dz1 = dh * (z1 > 0)
    return loss, {"W1": X.T @ dz1, "b1": dz1.sum(0), "W2": h.T @ dlogits, "b2": dlogits.sum(0)}


def compare(X, y, seed=0, verbose=True):
    """Compute the gradients both ways for one batch; return the biggest difference."""
    rng = np.random.default_rng(seed)
    np_params = {
        "W1": rng.standard_normal((X.shape[1], 128)) * np.sqrt(2 / X.shape[1]),
        "b1": rng.standard_normal(128) * 0.1,
        "W2": rng.standard_normal((128, 10)) * 0.1,
        "b2": rng.standard_normal(10) * 0.1,
    }

    # 1) Our numpy gradients
    np_loss, np_grads = numpy_loss_and_grads(**np_params, X=X, y=y)

    # 2) PyTorch: copy the SAME numbers into tensors that track gradients, then call backward()
    t = {name: torch.tensor(value, requires_grad=True) for name, value in np_params.items()}
    Xt, yt = torch.tensor(X), torch.tensor(y)
    logits = torch.relu(Xt @ t["W1"] + t["b1"]) @ t["W2"] + t["b2"]
    t_loss = F.cross_entropy(logits, yt)        # softmax + negative log likelihood + mean, in one call
    t_loss.backward()

    worst = max(np.abs(np_grads[n] - t[n].grad.numpy()).max() for n in np_grads)
    if verbose:
        print(f"loss   numpy {np_loss:.10f}   torch {t_loss.item():.10f}")
        for name in ["W1", "b1", "W2", "b2"]:
            diff = np.abs(np_grads[name] - t[name].grad.numpy()).max()
            print(f"d loss / d {name:<2}  shape {str(tuple(np_grads[name].shape)):<10}  biggest difference {diff:.2e}")
    return worst


if __name__ == "__main__":
    X_train, y_train, _, _ = load_mnist()
    X, y = X_train[:32].astype(np.float64), y_train[:32]   # float64 (double precision) so tiny rounding differences don't hide real bugs
    worst = compare(X, y)
    print("Our hand-written backprop matches PyTorch autograd." if worst < 1e-10 else "MISMATCH: check the backward pass!")
