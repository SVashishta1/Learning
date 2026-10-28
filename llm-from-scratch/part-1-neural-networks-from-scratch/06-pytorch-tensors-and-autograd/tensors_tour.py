"""Lesson 06, part 1: a guided tour of PyTorch tensors and autograd.

A tensor is a numpy array that can (a) run on a GPU and (b) remember how it was made,
so PyTorch can compute gradients for you, exactly like your micrograd Value but for whole arrays.
"""
import torch

torch.set_printoptions(precision=4)                     # print 4 decimals, so the output stays readable


def section(title):
    print("\n--- " + title + " ---")


section("1. Making tensors")
a = torch.tensor([[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]])     # from a Python list
print("a =", a)
print("shape:", a.shape, " dtype:", a.dtype, " device:", a.device)
print("zeros(2, 3):", torch.zeros(2, 3).tolist())
print("arange(5):", torch.arange(5).tolist())
g = torch.Generator().manual_seed(42)                    # a seeded random generator = repeatable "random" numbers
print("randn(2, 3) with seed 42:", torch.randn(2, 3, generator=g))

section("2. Indexing and reshaping")
print("a[0] (first row):", a[0].tolist())
print("a[:, 1] (second column):", a[:, 1].tolist())
print("a[1, 2] (one number):", a[1, 2].item())
print("a.view(3, 2):", a.view(3, 2).tolist(), " <- same 6 numbers, new shape")
print("a.view(-1):", a.view(-1).tolist(), " <- -1 means 'work this size out for me'")
print("a.T (transpose):", a.T.tolist())
rows = torch.tensor([1, 0, 1])
print("a[[1, 0, 1]] (pick rows by a list of indices):", a[rows].tolist())

section("3. Maths: element-wise, matrix multiply, broadcasting, sums")
print("a * 10:", (a * 10).tolist())
print("a @ a.T  (2x3 @ 3x2 -> 2x2):", (a @ a.T).tolist())
bias = torch.tensor([100.0, 200.0, 300.0])
print("a + bias (3,) is stretched to every row:", (a + bias).tolist())
print("a.sum():", a.sum().item(), " a.sum(0):", a.sum(0).tolist(), " a.sum(1, keepdim=True):", a.sum(1, keepdim=True).tolist())
print("softmax of row 0:", torch.softmax(a[0], dim=0))

section("4. Autograd on one number (the same neuron as lesson 03)")
x1 = torch.tensor(2.0, requires_grad=True)               # requires_grad=True: "track me, I want my gradient"
w1 = torch.tensor(-3.0, requires_grad=True)
b = torch.tensor(6.8813735870195432, requires_grad=True)
o = torch.tanh(x1 * w1 + b)
o.backward()                                             # fills .grad of every tracked tensor
print(f"o = {o.item():.4f}  do/dx1 = {x1.grad.item():.4f}  do/dw1 = {w1.grad.item():.4f}  do/db = {b.grad.item():.4f}")
print("o.grad_fn (the last operation PyTorch recorded):", type(o.grad_fn).__name__)

section("5. Autograd on a whole tensor")
x = torch.tensor([1.0, 2.0, 3.0], requires_grad=True)
y = (x**2).sum()                                         # y = x1^2 + x2^2 + x3^2, so dy/dx = 2x
y.backward()
print("x =", x.tolist(), " y = sum(x^2) =", y.item(), " dy/dx =", x.grad.tolist())

section("6. Gradients ADD UP: zero them between steps")
y = (x**2).sum()
y.backward()
print("after a second backward, x.grad =", x.grad.tolist(), " (doubled! same += as micrograd)")
x.grad = None                                            # what optimizer.zero_grad() does
y = (x**2).sum()
y.backward()
print("after clearing and one backward:", x.grad.tolist())

section("7. Turning tracking off")
with torch.no_grad():                                    # e.g. when updating weights or evaluating
    z = x * 2
print("inside no_grad: z.requires_grad =", z.requires_grad)
print("x.detach() gives the same numbers with tracking off: requires_grad =", x.detach().requires_grad)

section("8. Where can it run? (CPU, NVIDIA GPU, Apple GPU)")
if torch.cuda.is_available():
    device = "cuda"
elif torch.backends.mps.is_available():
    device = "mps"
else:
    device = "cpu"
print("best device on this machine:", device)
print("moving a tensor there:", a.to(device).device)

section("9. numpy <-> torch")
n = a.numpy()                                            # shares memory with a (CPU tensors only)
print("a.numpy() type:", type(n).__name__, " torch.from_numpy(...) type:", type(torch.from_numpy(n)).__name__)
