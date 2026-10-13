# 11 · One neuron learns

**What it does:** a "brain" with a single knob starts out wrong and teaches itself the rule "double the number" from 5 examples.

## Run it
```bash
cd part-3-neural-networks/11-one-neuron-learns
python one_neuron.py
```
Watch the knob creep from 0.5 to 2.0 while the bar of mistakes shrinks.

## The idea in one sentence
Guess → measure the mistake → turn the knob a little in the direction that shrinks the mistake → repeat. That loop is how **every** neural network learns.

## Try this
1. Set `step_size = 0.1`. The knob overshoots and goes crazy. Now you know why AI engineers fuss about the "learning rate".
2. Change the examples to follow "times 3" and watch it learn 3.
