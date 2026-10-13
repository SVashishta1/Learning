"""10 tiny exercises. Replace each `...` so the checks pass. Run: python warmup.py"""
import json
import random


def average(numbers):            # 1. average([2, 4, 6]) -> 4.0
    ...

def squared_errors(preds, targets):  # 2. [(p - t)**2 ...] for each pair
    ...

def word_counts(text):           # 3. "a b a" -> {"a": 2, "b": 1}
    ...

def only_positive(numbers):      # 4. keep numbers > 0 (use a list comprehension)
    ...

def pair_up(xs, ys):             # 5. [1,2],[3,4] -> [(1,3),(2,4)]
    ...

def top_k(scores, k):            # 6. {"cat": .9, "dog": .5, "eel": .7}, 2 -> ["cat", "eel"]
    ...

class Counter:                   # 7. c = Counter(); c.add(); c.add(); c.value == 2
    def __init__(self):
        ...
    def add(self):
        ...

def parse_user(json_text):       # 8. '{"name": "Ana", "age": 9}' -> "Ana is 9"
    ...

def shuffled_copy(items, seed):  # 9. return a shuffled COPY; original must not change
    ...

def report(epoch, loss):         # 10. report(3, 0.12345) -> "epoch 3 | loss 0.123"
    ...


CHECKS = [
    ("average", lambda: average([2, 4, 6]) == 4.0),
    ("squared_errors", lambda: squared_errors([1, 2], [1, 4]) == [0, 4]),
    ("word_counts", lambda: word_counts("a b a") == {"a": 2, "b": 1}),
    ("only_positive", lambda: only_positive([-1, 0, 3, 5]) == [3, 5]),
    ("pair_up", lambda: pair_up([1, 2], [3, 4]) == [(1, 3), (2, 4)]),
    ("top_k", lambda: top_k({"cat": .9, "dog": .5, "eel": .7}, 2) == ["cat", "eel"]),
    ("Counter", lambda: (lambda c: (c.add(), c.add(), c.value)[-1])(Counter()) == 2),
    ("parse_user", lambda: parse_user('{"name": "Ana", "age": 9}') == "Ana is 9"),
    ("shuffled_copy", lambda: (lambda xs: sorted(shuffled_copy(xs, 1)) == xs and xs == [1, 2, 3, 4])([1, 2, 3, 4])),
    ("report", lambda: report(3, 0.12345) == "epoch 3 | loss 0.123"),
]

if __name__ == "__main__":
    passed = 0
    for name, check in CHECKS:
        try:
            good = bool(check())
        except Exception as e:  # unfinished functions return None and may crash; that's fine
            good = False
        passed += good
        print(("✅" if good else "❌"), name)
    print(f"\n{passed}/{len(CHECKS)} done" + ("  🎉 You're ready for Level 1!" if passed == len(CHECKS) else ""))
