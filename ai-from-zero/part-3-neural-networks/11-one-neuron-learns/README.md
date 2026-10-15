# 11 · One neuron learns

**What you'll build:** a "brain" with a single knob that starts out wrong and teaches itself the rule "double the number" from 5 examples.
**Time:** ~30 min · **Builds on:** [Part 2 · Machine learning](../../part-2-machine-learning) (learning from examples) · **Needs:** nothing extra (plain Python)

## Why this matters
Every neural network, from a spam filter to Claude, learns with the loop you'll see here: guess, measure the mistake, nudge the knobs, repeat. In real jobs, a lot of time goes into tuning this loop, especially the **learning rate**. Seeing it work with one knob makes the big versions much less mysterious.

## What you'll learn
- **Weight (knob):** a number the model can change; here it's `w`, and the model's guess is `w × number`.
- **Mistake (error):** how far the guess is from the right answer.
- **Gradient (direction):** which way to turn the knob to make the mistakes smaller.
- **Learning rate (step size):** how big each nudge is. Too small is slow; too big makes it blow up.

## Before you start
- No packages to install. This is plain Python.
- No API key needed.
- Have your virtual environment on (see [00 · Start here](../../00-start-here)) so you're in the habit.

## Run it
1. Open a terminal in the `ai-from-zero` folder.
2. Go into this project and run it:
   ```bash
   cd part-3-neural-networks/11-one-neuron-learns
   python one_neuron.py
   ```
   (On a Mac, use `python3` if `python` isn't found.)

### What you should see
```
round  1: knob = 0.665   average miss = 4.500  ■■■■■■■■■■■■■■■■■■■■■■
round  2: knob = 0.812   average miss = 4.005  ■■■■■■■■■■■■■■■■■■■■
round  3: knob = 0.943   average miss = 3.564  ■■■■■■■■■■■■■■■■■
round  5: knob = 1.162   average miss = 2.823  ■■■■■■■■■■■■■■
round 10: knob = 1.532   average miss = 1.577  ■■■■■■■
round 20: knob = 1.854   average miss = 0.492  ■■
round 40: knob = 1.986   average miss = 0.048  
round 60: knob = 1.999   average miss = 0.005  

It learned w = 1.999 (the true rule is 2). So 7 → 13.99
```
Look at two things: the **knob** creeps from 0.5 towards 2.0, and the **bar of mistakes** shrinks to nothing. Nobody told it "2". It worked that out from the examples. Then it answers a question it never saw (7 → about 14).

## How it works
1. **The examples.** `examples = [(1, 2), (2, 4), ...]` is a list of (number, correct answer) pairs. This is the training data.
2. **The knob.** `w = 0.5` is a deliberately bad starting guess. The model's guess for any number is `w * number`, so right now it says 1 → 0.5.
3. **The step size.** `step_size = 0.01` controls how hard the knob is turned each round. AI engineers call this the **learning rate**.
4. **The loop runs 60 rounds.** Each round does three things:
   - **Guess and measure:** `mistakes` holds `guess - answer` for every example. Negative means "guessed too small".
   - **Find the direction:** `direction` is the average of `mistake × number`. Multiplying by the number makes sense: for big inputs, the knob has a big effect on the guess, so those examples get more say. This value is the **gradient**, the slope of "how wrong" with respect to the knob.
   - **Nudge:** `w = w - step_size * direction`. If guesses are too small, `direction` is negative, so subtracting it turns the knob **up**. If they're too big, it turns the knob **down**.
5. **Printing.** On a few chosen rounds it prints the knob, the average miss, and a bar whose length follows the miss (capped at 40 so it can't flood your screen).

Like walking downhill in fog: you can't see the bottom, but you can feel which way the ground slopes under your feet, so you take a small step that way, again and again.

```
guess (w × number) → measure mistakes → work out direction → nudge w → repeat
```

## If something goes wrong
- **`python: command not found`** (Mac/Linux) → use `python3 one_neuron.py`.
- **`can't open file 'one_neuron.py'`** → you're in the wrong folder. Run `cd part-3-neural-networks/11-one-neuron-learns` from the `ai-from-zero` folder first.
- **The knob shoots off to huge numbers like -84519** → your `step_size` is too big. Set it back to `0.01`.
- **The knob barely moves** → `step_size` is tiny (like `0.0001`) or you lowered the number of rounds. Raise one of them.

## Try this
1. **Change the step size.** Set `step_size = 0.1`, run it, then try `step_size = 0.2`.
   <details><summary>Hint</summary>

   With `0.1` it learns in about 3 rounds: bigger steps, faster learning. With `0.2` it overshoots, swings to the other side even further, and explodes (knob around -84,519 by round 60). There's a sweet spot: big enough to be quick, small enough to stay stable. That's why AI engineers fuss about the learning rate.
   </details>
2. **Teach it a new rule.** Change the examples so the answer is "times 3": `[(1, 3), (2, 6), (3, 9), (4, 12), (5, 15)]`. Also change the final message if you like.
   <details><summary>Hint</summary>

   The knob should end up near 3.0, and 7 → about 21. Same code, new data, new skill: that's machine learning.
   </details>
3. **Add a second knob.** Teach it "2 × number + 1" (examples `[(1, 3), (2, 5), (3, 7), (4, 9), (5, 11)]`). One knob can't do it, because `w × number` is always 0 when the number is 0. Add a knob `b` that's added to every guess.
   <details><summary>Solution</summary>

   ```python
   examples = [(1, 3), (2, 5), (3, 7), (4, 9), (5, 11)]   # rule: answer = 2 x number + 1
   w = 0.5
   b = 0.0                # the new knob: a fixed amount added to every answer ("bias")
   step_size = 0.01

   for round_number in range(1, 3001):
       mistakes = [(w * number + b - answer) for number, answer in examples]
       w = w - step_size * sum(m * number for m, (number, _) in zip(mistakes, examples)) / len(examples)
       b = b - step_size * sum(mistakes) / len(examples)

   print(f"w = {w:.3f}, b = {b:.3f}")
   ```
   It prints `w = 2.001, b = 0.997`. The extra knob is called a **bias**. Real neurons have one too.
   </details>

## Check yourself
1. What three steps happen in every round of training?
2. If the model's guesses are too **big**, which way does the knob turn, and why?
3. Why does a step size that's too large make things worse instead of faster?
4. Claude has billions of "knobs". How are they set?

<details><summary>Answers</summary>

1. Guess (and measure the mistakes), work out which way to turn the knob, nudge the knob a little that way.
2. Down. The mistakes are positive, so `direction` is positive, and `w - step_size * direction` makes `w` smaller.
3. Each step jumps past the right answer and lands even further away on the other side, so the mistakes grow every round instead of shrinking.
4. The same way: by this guess → measure → nudge loop, run on huge amounts of example text, with the maths for the "direction" worked out automatically.
</details>

## Learn more (optional)
- 3Blue1Brown, "Gradient descent, how neural networks learn": https://www.youtube.com/results?search_query=3blue1brown+gradient+descent+how+neural+networks+learn
- StatQuest, "Gradient Descent, Step-by-Step": https://www.youtube.com/results?search_query=statquest+gradient+descent+step+by+step

## Next
→ [12 · A tiny brain learns a puzzle](../12-tiny-brain-learns-a-puzzle)
