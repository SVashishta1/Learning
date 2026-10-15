# One "neuron" with ONE knob (w) learns the rule "answer = 2 x number", just from examples.
examples = [(1, 2), (2, 4), (3, 6), (4, 8), (5, 10)]   # (number, correct answer)

w = 0.5                # the knob starts at a bad guess
step_size = 0.01       # how hard to turn the knob each time ("learning rate")

for round_number in range(1, 61):
    # 1. Guess, and measure how wrong we are on every example
    mistakes = [(w * number - answer) for number, answer in examples]
    # 2. Which way should the knob turn? (If guesses are too small, mistakes are negative -> turn it UP.)
    direction = sum(m * number for m, (number, _) in zip(mistakes, examples)) / len(examples)
    # 3. Nudge the knob a little in the helpful direction
    w = w - step_size * direction
    if round_number in (1, 2, 3, 5, 10, 20, 40, 60):
        avg_miss = sum(abs(m) for m in mistakes) / len(mistakes)
        bar = "■" * min(int(avg_miss * 5), 40)        # a bar that shrinks with the mistakes (never longer than 40)
        print(f"round {round_number:2d}: knob = {w:.3f}   average miss = {avg_miss:.3f}  {bar}")

print(f"\nIt learned w = {w:.3f} (the true rule is 2). So 7 → {w * 7:.2f}")
