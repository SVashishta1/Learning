# Part 3 · Neural networks

**A neural network is a pile of adjustable knobs.** It makes a guess, checks how wrong it was, nudges every knob a tiny bit in the direction that makes it less wrong, and repeats thousands of times. That's "learning". ChatGPT and Claude are this, just with billions of knobs.

| # | Project | What happens | Time |
|---|---------|--------------|------|
| 11 | [One neuron learns](11-one-neuron-learns) | 1 knob learns "double the number", in plain Python | 30 min |
| 12 | [A tiny brain learns a puzzle](12-tiny-brain-learns-a-puzzle) | 2 layers of knobs solve a puzzle a single neuron can't | 45 min |
| 13 | [Same brain in PyTorch](13-same-brain-in-pytorch) | the professional tool does the hard maths for you | 40 min |
| 14 | [Read handwritten digits](14-read-handwritten-digits) | learns to read numbers from 60,000 real examples | 1 hour |
| 15 | [Draw-a-digit app](15-draw-a-digit-app) | draw a number in your browser; your model reads it live | 1 hour |

Do them in order. Each one reuses an idea from the one before.

## Install once
Turn on your virtual environment first (see [00 · Start here](../00-start-here)), then from the `ai-from-zero` folder:
```bash
pip install numpy torch torchvision pillow fastapi "uvicorn[standard]"
```
| Package | What it's for |
|---------|---------------|
| `numpy` | fast maths on whole tables of numbers (project 12) |
| `torch` | PyTorch, the tool real AI teams use to build neural networks (13–15) |
| `torchvision` | downloads the handwritten-digit pictures (14) |
| `pillow` | opens and resizes images (15) |
| `fastapi`, `uvicorn` | your web API from Part 1 (15) |

PyTorch is a big download (a few hundred MB), so give it a few minutes. You do **not** need a graphics card (GPU); everything here runs on a normal laptop.

## Words you'll meet
| Word | Plain meaning |
|------|---------------|
| **weight** (knob) | a number the network can adjust |
| **learning rate** (step size) | how far to turn the knobs each time |
| **loss** (mistake) | one number that says how wrong the guesses are |
| **layer** | a group of neurons that all take the same inputs |
| **epoch** (lap) | one pass through all the training examples |
| **training** | the guess → measure → nudge loop, repeated |

No API key needed for any of Part 3.
