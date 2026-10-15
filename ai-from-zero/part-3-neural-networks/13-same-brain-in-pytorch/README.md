# 13 · Same brain in PyTorch

**What you'll build:** the same XOR-solving brain as project 12, in about half the code. **PyTorch** does the blame maths for you.
**Time:** ~40 min · **Builds on:** [12 · A tiny brain learns a puzzle](../12-tiny-brain-learns-a-puzzle) · **Needs:** `torch`

## Why this matters
Nobody writes backpropagation by hand at work. Teams use PyTorch (or similar tools), describe the layers, and let it work out every knob's blame automatically. The 4-line training loop you'll learn here is the same one used to train models with billions of knobs, so once you know it you can read most real training code.

## What you'll learn
- **Tensor:** PyTorch's table of numbers (like a numpy array, but it can track how it was calculated).
- **Model as LEGO:** `torch.nn.Sequential` stacks layers such as `Linear` (knobs) and `Sigmoid` (squash).
- **Loss function:** turns "how wrong are all the guesses?" into one number (`MSELoss`).
- **Optimizer:** the tool that nudges every knob for you (`SGD`, `Adam`).
- **The training loop:** guess & measure → `zero_grad()` → `backward()` → `step()`.

## Before you start
- Install PyTorch, with your virtual environment on (it's a big download, a few hundred MB):
  ```bash
  pip install torch
  ```
  Or everything for Part 3: `pip install numpy torch torchvision pillow fastapi "uvicorn[standard]"`
- No API key and no graphics card needed.

## Run it
1. Open a terminal in the `ai-from-zero` folder.
2. Run:
   ```bash
   cd part-3-neural-networks/13-same-brain-in-pytorch
   python pytorch_brain.py
   ```

### What you should see
```
round 0: mistake 0.2544
round 1000: mistake 0.0029
round 2000: mistake 0.0009
round 3000: mistake 0.0005
round 4000: mistake 0.0003
round 5000: mistake 0.0003

What it learned:
  0, 0  →  0.02
  0, 1  →  0.98
  1, 0  →  0.98
  1, 1  →  0.02
```
It takes a few seconds (importing PyTorch is the slow part). The mistake falls towards 0 and the answers are close to 0, 1, 1, 0: the same result as project 12, without a single line of blame maths.

## How it works
1. **Data as tensors.** `torch.tensor([[0., 0.], ...])` makes the inputs and answers. The dots (`0.`) make them decimal numbers, which PyTorch needs for training.
2. **The model.** `torch.nn.Sequential(...)` stacks four bricks:
   - `Linear(2, 4)`: 2 inputs → 4 hidden neurons (like `knobs_1` in project 12, plus one extra "bias" knob per neuron).
   - `Sigmoid()`: the squash.
   - `Linear(4, 1)`: 4 hidden neurons → 1 answer.
   - `Sigmoid()`: squash the answer to between 0 and 1.
3. **`measure_mistake = torch.nn.MSELoss()`** is the loss function: the average of (guess − answer)², one number for "how wrong".
4. **`nudger = torch.optim.SGD(brain.parameters(), lr=2.0)`** is the optimizer. `brain.parameters()` hands it every knob; `lr` is the learning rate (step size). SGD stands for "stochastic gradient descent", the knob-nudging from project 11.
5. **The loop, 5,001 rounds of 4 lines:**
   1. `mistake = measure_mistake(brain(inputs), answers)`: guess and measure. PyTorch quietly records every calculation.
   2. `nudger.zero_grad()`: wipe last round's blame. (PyTorch *adds* new blame to old blame unless you clear it.)
   3. `mistake.backward()`: walk the recorded calculations backwards and work out every knob's blame. This replaces the three BLAME lines from project 12.
   4. `nudger.step()`: nudge every knob against its blame.
6. **Show the result.** `.detach()` says "just the numbers, stop recording", and `.item()` turns a one-number tensor into a normal Python number.

```
brain(inputs) → MSELoss → zero_grad() → backward() → step() → repeat
   guess        measure    clear blame    find blame    nudge
```

## If something goes wrong
- **`ModuleNotFoundError: No module named 'torch'`** → turn on your virtual environment and run `pip install torch`.
- **`pip install torch` fails or finds "no matching distribution"** → your Python may be too new or 32-bit. Use a recent 64-bit Python (3.10 or newer), or follow the install picker at https://pytorch.org (choose Pip, your OS, and CPU).
- **`RuntimeError: mat1 and mat2 must have the same dtype, but got Long and Float`** → you wrote the inputs without dots (`[0, 1]`), so they became whole numbers. Use `[0., 1.]`.
- **The mistake stays stuck near 0.25** → the learning rate is too small or the seed is unlucky. Try `lr=2.0`, more rounds, or the Adam optimizer (Try this #1).

## Try this
1. **Use a smarter nudger.** Replace `torch.optim.SGD(brain.parameters(), lr=2.0)` with `torch.optim.Adam(brain.parameters(), lr=0.05)`. Does it learn faster?
   <details><summary>Hint</summary>

   Yes: by round 1000 the mistake is about 0.0002 instead of 0.0029, and the answers come out as 0.00 / 1.00. Adam adjusts the step size for each knob automatically, which is why it's the default choice in most projects (including the next one).
   </details>
2. **Count the knobs.** Add `print(sum(p.numel() for p in brain.parameters()))` after the model is built. How many knobs are there, and why not 12 like project 12?
   <details><summary>Hint</summary>

   It prints 17. `Linear(2, 4)` has 2×4 = 8 weights plus 4 biases; `Linear(4, 1)` has 4 weights plus 1 bias. 8 + 4 + 4 + 1 = 17. Project 12 had no biases, so it had 12. When people say a model "has 70 billion parameters", this is what they're counting.
   </details>
3. **A harder puzzle: 3 inputs.** Teach it "answer 1 if an odd number of the 3 inputs are 1" (XOR for three inputs). You need 8 examples, 3 inputs, and a few more hidden neurons.
   <details><summary>Solution</summary>

   ```python
   import itertools

   import torch

   torch.manual_seed(0)
   rows = list(itertools.product([0., 1.], repeat=3))           # all 8 combinations of three 0/1 inputs
   inputs = torch.tensor(rows)
   answers = torch.tensor([[sum(r) % 2] for r in rows])          # 1 if an odd number of 1s

   brain = torch.nn.Sequential(
       torch.nn.Linear(3, 8), torch.nn.Sigmoid(),
       torch.nn.Linear(8, 1), torch.nn.Sigmoid(),
   )
   measure_mistake = torch.nn.MSELoss()
   nudger = torch.optim.Adam(brain.parameters(), lr=0.05)

   for round_number in range(3001):
       mistake = measure_mistake(brain(inputs), answers)
       nudger.zero_grad()
       mistake.backward()
       nudger.step()

   print("guesses:", brain(inputs).detach().round().flatten().tolist())
   print("answers:", answers.flatten().tolist())
   ```
   The two lines match: `[0.0, 1.0, 1.0, 0.0, 1.0, 0.0, 0.0, 1.0]`.
   </details>

## Check yourself
1. Which line in this project replaces the three BLAME lines from project 12?
2. What are the 4 steps of every PyTorch training loop, in order?
3. What does `nudger.zero_grad()` do, and why is it needed?
4. What's the difference between the loss function and the optimizer?

<details><summary>Answers</summary>

1. `mistake.backward()`. PyTorch records the calculations during the guess and works out every knob's blame automatically.
2. Guess and measure the loss → `zero_grad()` → `backward()` → `step()`.
3. It clears the blame from the previous round. PyTorch adds new blame on top of old blame, so without clearing, old rounds keep pushing the knobs. On this tiny puzzle it happens to still work, but on real models it usually ruins training.
4. The loss function *measures* how wrong the model is (one number). The optimizer *changes* the knobs to make that number smaller.
</details>

## Learn more (optional)
- PyTorch "Learn the Basics" tutorial: https://pytorch.org/tutorials/beginner/basics/intro.html
- Search: "PyTorch in 100 seconds" https://www.youtube.com/results?search_query=pytorch+in+100+seconds

## Next
→ [14 · Read handwritten digits](../14-read-handwritten-digits)
