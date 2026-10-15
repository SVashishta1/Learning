"""Reference answers. Try first! Run `python solutions.py` to see them pass the same checks as warmup.py."""
import json
import random


def average(numbers):
    return sum(numbers) / len(numbers)            # total divided by how many


def squared_errors(preds, targets):
    return [(p - t) ** 2 for p, t in zip(preds, targets)]   # zip walks both lists side by side


def word_counts(text):
    counts = {}
    for w in text.split():                        # "a b a" -> ["a", "b", "a"]
        counts[w] = counts.get(w, 0) + 1          # .get(w, 0): current count, or 0 if w is new
    return counts


def only_positive(numbers):
    return [n for n in numbers if n > 0]          # "give me n, for each n, but only if n > 0"


def pair_up(xs, ys):
    return list(zip(xs, ys))                      # zip gives pairs; list() collects them


def top_k(scores, k):
    # sorted() on a dict sorts its KEYS. key=scores.get means "sort keys by their score".
    return sorted(scores, key=scores.get, reverse=True)[:k]


class Counter:
    def __init__(self):
        self.value = 0                            # each Counter object remembers its own value

    def add(self):
        self.value += 1


def parse_user(json_text):
    d = json.loads(json_text)                     # JSON text -> Python dict
    return f"{d['name']} is {d['age']}"


def shuffled_copy(items, seed):
    copy = list(items)                            # a new list, so shuffling won't touch `items`
    random.Random(seed).shuffle(copy)             # same seed -> same shuffle every run
    return copy


def report(epoch, loss):
    return f"epoch {epoch} | loss {loss:.3f}"     # :.3f = 3 digits after the decimal point


if __name__ == "__main__":
    import warmup

    # Swap the unfinished functions in warmup.py for these answers, then run the same checks.
    for name in ["average", "squared_errors", "word_counts", "only_positive", "pair_up", "top_k",
                 "Counter", "parse_user", "shuffled_copy", "report"]:
        setattr(warmup, name, globals()[name])
    warmup.run_checks()
