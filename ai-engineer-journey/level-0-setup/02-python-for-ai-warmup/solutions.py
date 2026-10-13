"""Reference answers. Try first! Run `python solutions.py` to see them pass."""
import json
import random

def average(numbers): return sum(numbers) / len(numbers)
def squared_errors(preds, targets): return [(p - t) ** 2 for p, t in zip(preds, targets)]
def word_counts(text):
    counts = {}
    for w in text.split():
        counts[w] = counts.get(w, 0) + 1
    return counts
def only_positive(numbers): return [n for n in numbers if n > 0]
def pair_up(xs, ys): return list(zip(xs, ys))
def top_k(scores, k): return sorted(scores, key=scores.get, reverse=True)[:k]
class Counter:
    def __init__(self): self.value = 0
    def add(self): self.value += 1
def parse_user(json_text):
    d = json.loads(json_text)
    return f"{d['name']} is {d['age']}"
def shuffled_copy(items, seed):
    copy = list(items)
    random.Random(seed).shuffle(copy)
    return copy
def report(epoch, loss): return f"epoch {epoch} | loss {loss:.3f}"

if __name__ == "__main__":
    import warmup
    for name in ["average", "squared_errors", "word_counts", "only_positive", "pair_up", "top_k",
                 "Counter", "parse_user", "shuffled_copy", "report"]:
        setattr(warmup, name, globals()[name])
    for name, check in warmup.CHECKS:
        print(("✅" if check() else "❌"), name)
