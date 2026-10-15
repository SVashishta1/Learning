# 2.1 · One neuron learns y = 2x (plain Python)

**What you'll build:** a tiny "brain" with a single knob `w`. It predicts `w * x`, starts wrong (`w = 0.5`), and learns `w ≈ 2` by itself, using no libraries at all.
**Like you're 10:** you're throwing paper balls into a bin with your eyes closed. A friend says "too short!" or "too far!", and each time you adjust a bit. Soon you score every time. The friend's hint is the **gradient**; how much you adjust is the **learning rate**.
**Time:** ~45 min · **Builds on:** [0.2 · Python for AI warm-up](../../level-0-setup/02-python-for-ai-warmup) (Level 1 isn't needed here) · **Needs:** nothing extra

## Why this matters
Every neural network, from this one-knob toy to GPT, learns with the same loop: guess, measure the error, find which way to turn each knob, take a small step. GPT just has billions of knobs instead of one. If you understand these 40 lines, you understand what "training a model" means, and words like loss, gradient and learning rate will never be magic again.

## What you'll learn
- **Prediction:** the model's guess, here `w * x`.
- **Loss (error):** one number that says how wrong all the guesses are; here the **mean squared error**.
- **Gradient:** how much the loss changes when you nudge a knob, and in which direction ("uphill").
- **Gradient descent:** repeatedly step the knob *downhill*: `w = w - learning_rate * grad`.
- **Learning rate:** the step size. Too small is slow; too big overshoots and explodes.

## Before you start
- Nothing to install: plain Python (`requirements.txt` is empty on purpose).
- No API key needed.

## Run it
```bash
cd level-2-neural-nets-from-scratch/01-one-neuron-learns-y-equals-2x
python one_neuron.py
```

### What you should see
```
At w=0.5: error=24.75. Nudging w up changes error by -33.00 per unit.
Negative slope => increasing w REDUCES error. So we should move w UP.

step  1 | w = 0.8300 | error =  15.0579 ██████████████████████████████
step  2 | w = 1.0874 | error =   9.1612 ██████████████████
step  3 | w = 1.2882 | error =   5.5737 ███████████
step  5 | w = 1.5669 | error =   2.0631 ████
step 10 | w = 1.8750 | error =   0.1720
step 20 | w = 1.9896 | error =   0.0012
step 40 | w = 1.9999 | error =   0.0000
step 60 | w = 2.0000 | error =   0.0000

Learned w = 2.0000 (truth is 2). Prediction for x=10: 20.00

With learning_rate=0.1 after 10 steps, w = -7.3  <- exploded! Steps too big overshoot the valley.
```
Watch three things: the error bar shrinks, `w` creeps toward 2 (fast at first, then slower as the slope flattens), and with a learning rate of 0.1, `w` runs away instead.

## How it works
```
      guess            measure           which way?             step
w ──► w * x ──► mean of (w*x - y)^2 ──► grad = d(error)/dw ──► w = w - 0.01 * grad ──┐
▲                                                                                     │
└──────────────────────────────────── repeat 60 times ◄───────────────────────────────┘
```
1. **The data:** `data = [(x, 2 * x) for x in [1, 2, 3, 4, 5]]` gives the pairs `(1, 2), (2, 4), ... (5, 10)`. The model never sees the rule "times 2", only these examples.
2. **`total_error(w)`** is the **mean squared error**: for each example, take `prediction - truth`, square it (so negatives don't cancel positives, and big mistakes count extra), then average.
3. **Step 0, the nudge test:** `slope = (total_error(w + nudge) - total_error(w)) / nudge`. Move `w` up by a tiny `0.0001` and see how the error changes. At `w = 0.5` the slope is `-33`: increasing `w` makes the error go *down*. That slope **is** the gradient. This is the most important idea in deep learning: *a gradient answers "if I wiggle this knob, how does the error change?"*
4. **Step 1, the learning loop:** instead of nudging, we use calculus to get the exact slope in one go: `grad = average of 2 * (w*x - y) * x` (the derivative of the squared error). Then `w = w - learning_rate * grad`. The minus sign means "go opposite to uphill", i.e. downhill. With `learning_rate = 0.01`, each step moves `w` a fraction of the way.
5. **Why it slows down:** near `w = 2` the error valley is almost flat, so `grad` is small and the steps get small too. No special code needed; it falls out of the formula.
6. **Step 2, a bad learning rate:** with `0.1`, each step jumps *past* the bottom of the valley to a point even higher up the other side, so `w` swings further away every time and explodes.

## If something goes wrong
- **`python: can't open file 'one_neuron.py'`** → you're not in the project folder. Run the `cd` line first (from the course root `ai-engineer-journey`).
- **`python: command not found`** → on macOS/Linux try `python3 one_neuron.py`, or activate your venv from 0.1.
- **The bars print as `?` or boxes** → your terminal font lacks the `█` character. Ignore it (the numbers are what matter) or use VS Code's terminal.
- **After your edits `w` becomes `nan` or `inf`** → the learning rate is too big for your data, so it exploded. Make it 10x smaller.
- **`w` barely moves** → the learning rate is too small, or the loop is too short. Raise one of them.

## Try this
1. Find the largest learning rate that still works. Try 0.03, 0.05, 0.08, 0.09 and 0.1 in the loop of Step 1.
   <details><summary>Answer</summary>

   0.03, 0.05 and 0.08 all reach `w = 2.0` in 60 steps (0.08 overshoots back and forth but settles). 0.09 is still crawling there (`w ≈ 1.55` after 60 steps). 0.1 explodes. For this data the limit is `2 / 22 ≈ 0.091`: the gradient is `22 * (w - 2)`, and steps bigger than that limit overshoot by more than they correct.
   </details>
2. Replace the calculus gradient in the learning loop with the "nudge" formula from Step 0. Does it still learn?
   <details><summary>Solution</summary>

   ```python
   w = 0.5
   for step in range(1, 61):
       grad = (total_error(w + nudge) - total_error(w)) / nudge   # numerical gradient
       w = w - learning_rate * grad
   ```
   It learns almost exactly the same (`w = 1.9999`). This is a **numerical gradient**. The catch: it needs extra error calculations for *every* knob. With a billion knobs that's hopeless, which is why real frameworks use the calculus way (backpropagation, 2.3).
   </details>
3. Learn `y = 3x + 1`. You need a second knob `b` (bias): `prediction = w*x + b`, and the gradient for `b` is the average of `2 * (prediction - y)`.
   <details><summary>Solution</summary>

   ```python
   data = [(x, 3 * x + 1) for x in [1, 2, 3, 4, 5]]
   w, b = 0.5, 0.0
   learning_rate = 0.01
   for step in range(1, 2001):
       grad_w = sum(2 * (w * x + b - y) * x for x, y in data) / len(data)
       grad_b = sum(2 * (w * x + b - y) for x, y in data) / len(data)
       w -= learning_rate * grad_w
       b -= learning_rate * grad_b
   print(f"w = {w:.3f}, b = {b:.3f}")   # w = 3.000, b = 1.000
   ```
   It needs many more steps (2,000) because `b` learns slowly at this learning rate. Every neuron in a real network has exactly these two kinds of knobs: weights and a bias.
   </details>

## Check yourself
1. What does the gradient tell you, in plain words?
2. Why do we *subtract* `learning_rate * grad` instead of adding it?
3. Why do the steps get smaller near the answer, even though the learning rate never changes?
4. What happens with a learning rate that's too big, and why?

<details><summary>Answers</summary>

1. How much the error changes if you nudge the knob up a little, and in which direction. Negative means "increasing the knob reduces the error".
2. The gradient points uphill (towards more error). Subtracting it moves the knob downhill, towards less error.
3. The step is `learning_rate * grad`, and the gradient gets smaller as the error valley flattens out near the bottom.
4. Each step jumps past the bottom of the valley to a point that's even worse on the other side, so the error grows every step and `w` explodes.
</details>

## Learn more (optional)
- Gradient descent, how neural networks learn (3Blue1Brown): https://www.youtube.com/results?search_query=3blue1brown+gradient+descent+how+neural+networks+learn
- Gradient descent step by step (StatQuest): https://www.youtube.com/results?search_query=statquest+gradient+descent+step+by+step

## Next
→ [2.2 · Forward pass: two-layer network in NumPy](../02-forward-pass-two-layer-network-numpy)
