# 08 · Flower guesser

**What it does:** guesses which of 3 types of iris flower you have from 4 measurements, and prints the exact if/else questions it learned.

## Run it
```bash
cd part-2-machine-learning/08-flower-guesser
python flower_guesser.py
python flower_guesser.py 5.0 3.4 1.5 0.2
```

## The idea in one sentence
A **decision tree** learns the best yes/no questions to ask ("is the petal width ≤ 0.8 cm?"), like a game of 20 Questions, and you can read its reasoning.

## Try this
1. Change `max_depth=3` to `1`. How many questions can it ask now? Are its guesses worse?
2. Follow the printed rules by hand for `5.0 3.4 1.5 0.2`. Do you get the same answer as the model?
