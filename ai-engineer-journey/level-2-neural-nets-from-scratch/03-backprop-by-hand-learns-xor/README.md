# 2.3 · Backpropagation by hand: learn XOR

**What you build:** a 2 → 4 → 1 network that learns XOR. You write **every gradient yourself** with the chain rule, then prove it's right with a gradient check.
**Like you're 10:** a team lost a game. The coach (backprop) walks backwards from the final score: "the striker missed because the midfielder's pass was late, because the defender..." Everyone learns *their own* share of the blame and practises just that.

## Run it
```bash
cd level-2-neural-nets-from-scratch/03-backprop-by-hand-learns-xor
pip install -r requirements.txt
python backprop_xor.py
```
Expected: the gradient check matches, the loss drops from ~0.25 to ~0.001, and all four XOR cases get ✅.

## Key ideas
- **Chain rule:** if the loss depends on `p`, `p` on `z2`, and `z2` on `W2`, then `dLoss/dW2 = dLoss/dp × dp/dz2 × dz2/dW2`. Backprop just applies this from the end to the start, reusing pieces.
- **Gradient check:** always verify hand-written gradients with the nudge method. Engineers really do this when writing new layers.
- **Why XOR?** No single straight line separates XOR's 1s from its 0s. The hidden layer bends the space so that one line works. That is *why* depth matters.

## Your turn
1. Change the hidden size from 4 to 2. Does it still learn? (Sometimes! Try different seeds.)
2. Try `lr = 0.1` and `lr = 10`. Plot loss vs. epoch with matplotlib.
3. Add a gradient check for `W2` too.

## Watch
- What is backpropagation really doing? (3Blue1Brown): https://www.youtube.com/results?search_query=3blue1brown+what+is+backpropagation+really+doing
- Backpropagation calculus (3Blue1Brown): https://www.youtube.com/results?search_query=3blue1brown+backpropagation+calculus
