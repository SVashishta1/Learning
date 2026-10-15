"""10 tiny exercises. Replace each `...` with real code so the checks pass. Run: python warmup.py

Each function has a comment showing an example input and the answer it should give.
Work top to bottom, re-run after every exercise, and only peek at solutions.py after a real try.
"""
import json
import random


def average(numbers):            # 1. average([2, 4, 6]) -> 4.0      (hint: sum() and len())
    ...

def squared_errors(preds, targets):  # 2. ([1, 2], [1, 4]) -> [0, 4]   i.e. (p - t) ** 2 for each pair
    ...

def word_counts(text):           # 3. "a b a" -> {"a": 2, "b": 1}     (hint: text.split() and a dict)
    ...

def only_positive(numbers):      # 4. [-1, 0, 3, 5] -> [3, 5]  keep numbers > 0 (use a list comprehension)
    ...

def pair_up(xs, ys):             # 5. [1, 2], [3, 4] -> [(1, 3), (2, 4)]   (hint: zip)
    ...

def top_k(scores, k):            # 6. {"cat": .9, "dog": .5, "eel": .7}, 2 -> ["cat", "eel"]  highest scores first
    ...

class Counter:                   # 7. c = Counter(); c.add(); c.add(); c.value == 2
    def __init__(self):
        ...                      #    start the count at 0 (store it on self)
    def add(self):
        ...                      #    add 1 to the count

def parse_user(json_text):       # 8. '{"name": "Ana", "age": 9}' -> "Ana is 9"   (hint: json.loads)
    ...

def shuffled_copy(items, seed):  # 9. return a shuffled COPY; the original list must not change
    ...                          #    (hint: list(items) makes a copy; random.Random(seed).shuffle(...) shuffles it)

def report(epoch, loss):         # 10. report(3, 0.12345) -> "epoch 3 | loss 0.123"   (hint: f"{loss:.3f}")
    ...


# ---------------------------------------------------------------------------------------------
# The checker. You don't need to change anything below this line (but reading it is good practice).
# Each check returns (what your code gave, what it should give).

def check_counter():
    c = Counter()
    c.add()
    c.add()
    return c.value, 2


def check_shuffled_copy():
    original = [1, 2, 3, 4]
    result = shuffled_copy(original, 1)
    # Same numbers, a NEW list, and the original untouched:
    return (sorted(result), result is not original, original), ([1, 2, 3, 4], True, [1, 2, 3, 4])


CHECKS = [
    ("1 average", lambda: (average([2, 4, 6]), 4.0)),
    ("2 squared_errors", lambda: (squared_errors([1, 2], [1, 4]), [0, 4])),
    ("3 word_counts", lambda: (word_counts("a b a"), {"a": 2, "b": 1})),
    ("4 only_positive", lambda: (only_positive([-1, 0, 3, 5]), [3, 5])),
    ("5 pair_up", lambda: (pair_up([1, 2], [3, 4]), [(1, 3), (2, 4)])),
    ("6 top_k", lambda: (top_k({"cat": .9, "dog": .5, "eel": .7}, 2), ["cat", "eel"])),
    ("7 Counter", check_counter),
    ("8 parse_user", lambda: (parse_user('{"name": "Ana", "age": 9}'), "Ana is 9")),
    ("9 shuffled_copy", check_shuffled_copy),
    ("10 report", lambda: (report(3, 0.12345), "epoch 3 | loss 0.123")),
]


def run_checks():
    passed = 0
    for name, check in CHECKS:
        try:
            got, want = check()
            good = got == want
            note = "" if good else f"   got {got!r}, want {want!r}"
        except Exception as e:  # unfinished code often crashes; we show the error and keep going
            good, note = False, f"   crashed: {type(e).__name__}: {e}"
        passed += good
        print(("✅ " if good else "❌ ") + name + note)
    print(f"\n{passed}/{len(CHECKS)} done" + ("  🎉 You're ready for Level 1!" if passed == len(CHECKS) else ""))
    return passed


if __name__ == "__main__":
    run_checks()
