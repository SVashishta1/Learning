# 2.1 · One neuron learns y = 2x (plain Python, zero libraries)

**What you build:** a tiny "brain" with a single knob `w`. It predicts `w * x`, starts wrong (`w = 0.5`), and learns `w ≈ 2` by itself.
**Like you're 10:** you're throwing paper balls into a bin with your eyes closed. A friend says "too short!" or "too far!". Each time you adjust a bit. Soon you score every time. The friend's hint is the **gradient**; how much you adjust is the **learning rate**.

## Run it
```bash
cd level-2-neural-nets-from-scratch/01-one-neuron-learns-y-equals-2x
python one_neuron.py
```
You'll see the error bar shrink step by step, `w` creep toward 2, and then a too-big learning rate blow up.

## Key ideas
| Word | Meaning | In the code |
|------|---------|-------------|
| prediction | the guess | `w * x` |
| loss / error | how wrong, as one number | `total_error(w)` (mean squared error) |
| gradient | which way is uphill, and how steep | `grad` |
| gradient descent | walk downhill | `w = w - learning_rate * grad` |
| learning rate | step size | `0.01` |

The **nudge test** at the top is the most important idea in deep learning: *a gradient answers "if I wiggle this knob, how does the error change?"*

## Your turn
1. Learn `y = 3x + 1`. You need a second knob `b` (bias): `prediction = w*x + b`, and the gradient for `b` is `avg(2 * (pred - y))`.
2. Find the largest learning rate that still works (try 0.03, 0.05, 0.08).
3. Replace the calculus gradient with the "nudge" formula for every step. Does it still learn? (Yes, just slower. That's *numerical* gradients.)

## Watch
- Gradient descent, how neural networks learn (3Blue1Brown): https://www.youtube.com/results?search_query=3blue1brown+gradient+descent+how+neural+networks+learn
- Gradient descent step by step (StatQuest): https://www.youtube.com/results?search_query=statquest+gradient+descent+step+by+step
