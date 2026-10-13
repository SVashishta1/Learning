# 12 · A tiny brain learns a puzzle

**What it does:** a 2-layer neural network teaches itself the XOR puzzle (answer 1 only when exactly one input is 1). It starts by guessing randomly and ends up almost perfect.

## Run it
```bash
cd part-3-neural-networks/12-tiny-brain-learns-a-puzzle
python tiny_brain.py
```

## The idea in one sentence
Same loop as project 11 (guess → blame → nudge) but with two **layers** of knobs; the hidden layer lets it learn patterns that aren't a simple straight-line rule.

Don't worry about the three "BLAME" lines. They're the calculus that hands out blame, and in the next project PyTorch writes them for you automatically.

## Try this
1. Change `randn(2, 4)` and `randn(4, 1)` to `randn(2, 2)` and `randn(2, 1)`. Fewer hidden neurons: does it still learn?
2. Change the answers to `[[0], [0], [0], [1]]` (AND: both must be 1) and see it learn that instead.

## Watch (optional, beautiful visuals)
- 3Blue1Brown, "But what is a neural network?": https://www.youtube.com/results?search_query=3blue1brown+but+what+is+a+neural+network
