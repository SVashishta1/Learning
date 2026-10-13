"""Project 2.5: build the SAME XOR network twice (your NumPy code vs PyTorch), with the SAME starting
weights, and prove the outputs, gradients and training curves match."""
import numpy as np
import torch

rng = np.random.default_rng(42)
X_np = np.array([[0, 0], [0, 1], [1, 0], [1, 1]], dtype=np.float64)
Y_np = np.array([[0], [1], [1], [0]], dtype=np.float64)
W1_np, b1_np = rng.normal(0, 1, (2, 4)), np.zeros(4)
W2_np, b2_np = rng.normal(0, 1, (4, 1)), np.zeros(1)

# ---------- Version A: NumPy, gradients by hand (same as project 2.3) ----------
sig = lambda z: 1 / (1 + np.exp(-z))


def numpy_step(W1, b1, W2, b2, lr):
    h = sig(X_np @ W1 + b1)
    p = sig(h @ W2 + b2)
    loss = np.mean((p - Y_np) ** 2)
    dz2 = 2 * (p - Y_np) / len(X_np) * p * (1 - p)
    dW2, db2 = h.T @ dz2, dz2.sum(0)
    dz1 = dz2 @ W2.T * h * (1 - h)
    dW1, db1 = X_np.T @ dz1, dz1.sum(0)
    return loss, (dW1, db1, dW2, db2), (W1 - lr * dW1, b1 - lr * db1, W2 - lr * dW2, b2 - lr * db2)


# ---------- Version B: PyTorch, gradients by autograd ----------
class XorNet(torch.nn.Module):
    def __init__(self):
        super().__init__()
        self.hidden = torch.nn.Linear(2, 4)
        self.out = torch.nn.Linear(4, 1)

    def forward(self, x):
        return torch.sigmoid(self.out(torch.sigmoid(self.hidden(x))))


model = XorNet().double()
with torch.no_grad():   # copy our NumPy weights in. Note: PyTorch stores Linear weights TRANSPOSED (out, in)
    model.hidden.weight.copy_(torch.tensor(W1_np.T)); model.hidden.bias.copy_(torch.tensor(b1_np))
    model.out.weight.copy_(torch.tensor(W2_np.T)); model.out.bias.copy_(torch.tensor(b2_np))

X_t, Y_t = torch.tensor(X_np), torch.tensor(Y_np)
optimizer = torch.optim.SGD(model.parameters(), lr=2.0)
loss_fn = torch.nn.MSELoss()

# ---------- Compare step 1 gradients ----------
loss_np, grads_np, _ = numpy_step(W1_np, b1_np, W2_np, b2_np, lr=2.0)
loss_t = loss_fn(model(X_t), Y_t)
loss_t.backward()                       # <- autograd computes ALL gradients for us
print(f"loss      numpy {loss_np:.10f} | torch {loss_t.item():.10f}")
print("dW1 match:", np.allclose(grads_np[0], model.hidden.weight.grad.numpy().T))
print("dW2 match:", np.allclose(grads_np[2], model.out.weight.grad.numpy().T))

# ---------- Train both for 3000 steps and compare ----------
params = (W1_np, b1_np, W2_np, b2_np)
optimizer.zero_grad()
for step in range(1, 3001):
    loss_np, _, params = numpy_step(*params, lr=2.0)
    optimizer.zero_grad()                # gradients ADD UP in PyTorch unless you reset them
    loss_t = loss_fn(model(X_t), Y_t)
    loss_t.backward()
    optimizer.step()
    if step in (1, 1000, 3000):
        print(f"step {step:4d} | numpy loss {loss_np:.6f} | torch loss {loss_t.item():.6f}")

print("\nFinal predictions (numpy vs torch):")
h = sig(X_np @ params[0] + params[1]); p_np = sig(h @ params[2] + params[3]).ravel()
p_t = model(X_t).detach().numpy().ravel()
for xi, a, b in zip(X_np.astype(int), p_np, p_t):
    print(f"  {xi}: {a:.4f} vs {b:.4f}")
assert np.allclose(p_np, p_t, atol=1e-6)
print("\n✅ Your hand-written backprop and PyTorch's autograd agree.")
