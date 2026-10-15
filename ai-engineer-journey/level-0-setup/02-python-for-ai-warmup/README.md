# 0.2 · Python for AI warm-up

**What you'll build:** 10 tiny Python functions (averages, word counts, sorting, a class, JSON and more), checked automatically by a script that tells you what's right and what's wrong.
**Like you're 10:** scales and finger exercises before playing a song. Boring for 5 minutes, then every song is easier.
**Time:** ~1 h · **Builds on:** [0.1 · Set up your AI workbench](../01-setup-your-ai-workbench) · **Needs:** nothing extra (plain Python)

## Why this matters
AI code is mostly ordinary Python: averaging losses, counting words, pairing inputs with labels, sorting search results, reading JSON from an API. These 10 exercises are the 20% of Python that shows up in 80% of the code in this course. If you can do them without looking, Levels 1 and 2 will feel much easier.

## What you'll learn
- **Lists and loops:** a list holds many values in order; `sum()`, `len()` and `for` work through them.
- **Dicts:** a dict maps keys to values (`{"cat": 0.9}`), exactly the shape of JSON.
- **List comprehensions:** `[x * 2 for x in nums if x > 0]` builds a new list in one readable line.
- **Classes:** a class bundles data and the functions that use it (`self.value`, `add()`); Level 2's layers are classes.
- **JSON, random and f-strings:** read API data, shuffle data reproducibly, and print neat logs.

## Before you start
- No packages to install: everything used here (`json`, `random`) comes with Python.
- Activate your venv from 0.1 (your prompt starts with `(.venv)`).
- No API key needed.

## Run it
1. Go to the folder and run the checker:
   ```bash
   cd level-0-setup/02-python-for-ai-warmup
   python warmup.py
   ```
2. Open `warmup.py` in VS Code. Each exercise is a function with `...` in its body. Replace `...` with your code.
3. Save and run `python warmup.py` again. Repeat until all 10 are ✅.
4. Stuck for more than 5 minutes? Open the matching **Solution** below, or run `python solutions.py` to see the reference answers pass.

### What you should see
At the start, every exercise fails and tells you what it got and what it wanted:
```
❌ 1 average   got None, want 4.0
❌ 2 squared_errors   got None, want [0, 4]
❌ 3 word_counts   got None, want {'a': 2, 'b': 1}
❌ 4 only_positive   got None, want [3, 5]
❌ 5 pair_up   got None, want [(1, 3), (2, 4)]
❌ 6 top_k   got None, want ['cat', 'eel']
❌ 7 Counter   crashed: AttributeError: 'Counter' object has no attribute 'value'
❌ 8 parse_user   got None, want 'Ana is 9'
❌ 9 shuffled_copy   crashed: TypeError: 'NoneType' object is not iterable
❌ 10 report   got None, want 'epoch 3 | loss 0.123'

0/10 done
```
`got None` means your function doesn't `return` anything yet. When you've finished:
```
✅ 1 average
✅ 2 squared_errors
...
✅ 10 report

10/10 done  🎉 You're ready for Level 1!
```

## How it works
1. **The exercises** (top of `warmup.py`): each function has a comment with an example input, the answer it should give and a hint.
2. **`CHECKS`** is a list of `(name, check)` pairs. Each `check` is a small function that calls your code and returns two things: what your code gave (`got`) and the right answer (`want`). `lambda: (average([2, 4, 6]), 4.0)` is just a one-line function with no name.
3. **`check_counter()` and `check_shuffled_copy()`** need a few lines, so they are normal functions. The shuffle check confirms you returned a *new* list (`result is not original`) and left the original alone.
4. **`run_checks()`** loops over `CHECKS`, compares `got == want`, and prints ✅ or ❌. The `try/except` catches crashes from unfinished code so one broken exercise doesn't stop the rest.
5. **`solutions.py`** holds reference answers. Its `__main__` block swaps them into `warmup` with `setattr` and calls the same `run_checks()`, so you can see the checker pass.

| # | Skill | Where you'll use it later |
|---|-------|---------------------------|
| 1-2 | lists, `sum`/`len`, `zip` | computing averages and loss values (Level 2) |
| 3 | dicts | JSON from APIs (Level 1), word counts (Level 5) |
| 4 | list comprehensions | data cleaning |
| 5 | `zip` | pairing inputs with labels |
| 6 | sorting with `key=` | ranking search results (Level 7 RAG) |
| 7 | classes | `Layer` and `Neuron` classes (Level 2) |
| 8 | `json` | every API in Level 1 |
| 9 | `random` | shuffling training data |
| 10 | f-strings | readable training logs |

### Solutions (try first!)
<details><summary>1 · average</summary>

```python
def average(numbers):
    return sum(numbers) / len(numbers)
```
`sum` adds them up, `len` counts them. In Python 3, `/` always gives a float, so you get `4.0`.
</details>

<details><summary>2 · squared_errors</summary>

```python
def squared_errors(preds, targets):
    return [(p - t) ** 2 for p, t in zip(preds, targets)]
```
`zip` walks both lists side by side: `(1, 1)`, then `(2, 4)`. Squaring makes every error positive. This is the heart of "mean squared error" in Level 2.
</details>

<details><summary>3 · word_counts</summary>

```python
def word_counts(text):
    counts = {}
    for w in text.split():
        counts[w] = counts.get(w, 0) + 1
    return counts
```
`text.split()` breaks the text on spaces. `counts.get(w, 0)` returns the current count, or 0 the first time a word appears.
</details>

<details><summary>4 · only_positive</summary>

```python
def only_positive(numbers):
    return [n for n in numbers if n > 0]
```
Read it as: "give me `n`, for each `n` in `numbers`, but only if `n > 0`". Zero is not positive, so it's dropped.
</details>

<details><summary>5 · pair_up</summary>

```python
def pair_up(xs, ys):
    return list(zip(xs, ys))
```
`zip` produces pairs lazily (one at a time); `list()` collects them into a list of tuples.
</details>

<details><summary>6 · top_k</summary>

```python
def top_k(scores, k):
    return sorted(scores, key=scores.get, reverse=True)[:k]
```
`sorted(scores)` sorts the dict's keys. `key=scores.get` says "sort each key by its score", `reverse=True` puts the highest first, and `[:k]` keeps the first `k`.
</details>

<details><summary>7 · Counter</summary>

```python
class Counter:
    def __init__(self):
        self.value = 0
    def add(self):
        self.value += 1
```
`__init__` runs when you write `Counter()`. `self` is "this particular counter", so two counters keep separate values.
</details>

<details><summary>8 · parse_user</summary>

```python
def parse_user(json_text):
    d = json.loads(json_text)
    return f"{d['name']} is {d['age']}"
```
`json.loads` ("load string") turns JSON text into a Python dict. Inside an f-string, use single quotes for the keys because the f-string uses double quotes.
</details>

<details><summary>9 · shuffled_copy</summary>

```python
def shuffled_copy(items, seed):
    copy = list(items)
    random.Random(seed).shuffle(copy)
    return copy
```
`shuffle` changes a list *in place* and returns `None`, so shuffle a copy and return the copy. `random.Random(seed)` is a random generator that gives the same "random" order every run for the same seed, which makes experiments repeatable.
</details>

<details><summary>10 · report</summary>

```python
def report(epoch, loss):
    return f"epoch {epoch} | loss {loss:.3f}"
```
`:.3f` means "a float with 3 digits after the decimal point", so `0.12345` prints as `0.123`.
</details>

## If something goes wrong
- **Everything says `got None`** → your function needs `return`. Printing a value is not the same as returning it.
- **`IndentationError` or `SyntaxError`** → the body of a function must be indented 4 spaces under the `def` line. VS Code shows the bad line with a red squiggle.
- **`7 Counter crashed: AttributeError ... no attribute 'value'`** → set `self.value = 0` inside `__init__` (not just `value = 0`).
- **`9 shuffled_copy` fails with `got ([1, 2, 3, 4], False, ...)`** → you returned the original list instead of a copy. Use `copy = list(items)` first.
- **`python: can't open file 'warmup.py'`** → you're in the wrong folder. Run `cd level-0-setup/02-python-for-ai-warmup` from the course root.

## Try this
1. Add an 11th exercise: `def maximum(numbers)` that returns the biggest number *without* using `max()`, and add a check for it to `CHECKS`.
   <details><summary>Solution</summary>

   ```python
   def maximum(numbers):
       best = numbers[0]
       for n in numbers[1:]:
           if n > best:
               best = n
       return best
   ```
   Then add `("11 maximum", lambda: (maximum([3, 9, 2]), 9)),` to the `CHECKS` list.
   </details>
2. Write `normalise(numbers)` that scales a list so it sums to 1: `[1, 1, 2]` → `[0.25, 0.25, 0.5]`. (This is how probabilities are made in AI models.)
   <details><summary>Solution</summary>

   ```python
   def normalise(numbers):
       total = sum(numbers)
       return [n / total for n in numbers]
   ```
   </details>
3. Write `accuracy(preds, labels)` that returns the fraction of positions where the prediction equals the label: `accuracy([1, 0, 1, 1], [1, 1, 1, 0])` → `0.5`. Use `zip` and a comprehension.
   <details><summary>Solution</summary>

   ```python
   def accuracy(preds, labels):
       return sum(p == y for p, y in zip(preds, labels)) / len(labels)
   ```
   `p == y` is `True` or `False`, and Python counts `True` as 1 when you `sum` them.
   </details>

## Check yourself
1. What's the difference between `print(x)` and `return x` inside a function?
2. Why does `shuffled_copy` copy the list before shuffling?
3. What does `sorted(scores, key=scores.get)` sort, and by what?
4. In `class Counter`, why do we write `self.value` and not just `value`?

<details><summary>Answers</summary>

1. `print` shows `x` on the screen and the function still returns `None`. `return` hands `x` back to whoever called the function, so the caller can use it.
2. `shuffle` changes the list it's given. Without a copy, the caller's original list would be scrambled too (a classic data bug).
3. It sorts the dict's keys (the words), using each key's value (its score) as the thing to compare.
4. `self.value` is stored on the object, so it survives between calls to `add()`. A plain `value` would be a local variable that disappears when the method ends.
</details>

## Learn more (optional)
- Python for Beginners (freeCodeCamp, full course): https://www.youtube.com/results?search_query=freecodecamp+python+for+beginners+full+course
- The official Python tutorial (sections 3 to 5 cover everything here): https://docs.python.org/3/tutorial/

## Next
→ [1.1 · Hello API: the waiter says hi](../../level-1-apis/01-hello-api-the-waiter-says-hi)
