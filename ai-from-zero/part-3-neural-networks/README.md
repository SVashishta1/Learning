# Part 3 · Neural networks

**A neural network is a pile of adjustable knobs.** It makes a guess, checks how wrong it was, nudges every knob a tiny bit in the direction that makes it less wrong, and repeats thousands of times. That's "learning". ChatGPT and Claude are this, just with billions of knobs.

| # | Project | What happens |
|---|---------|--------------|
| 11 | [One neuron learns](11-one-neuron-learns) | 1 knob learns "double the number", in plain Python |
| 12 | [A tiny brain learns a puzzle](12-tiny-brain-learns-a-puzzle) | 2 layers of knobs solve a puzzle a single neuron can't |
| 13 | [Same brain in PyTorch](13-same-brain-in-pytorch) | the professional tool does the hard maths for you |
| 14 | [Read handwritten digits](14-read-handwritten-digits) | learns to read numbers from 60,000 real examples |
| 15 | [Draw-a-digit app](15-draw-a-digit-app) | draw a number in your browser; your model reads it live |

Install once:
```bash
pip install numpy torch torchvision pillow fastapi "uvicorn[standard]"
```
