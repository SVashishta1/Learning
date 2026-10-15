# 08 · Flower guesser

**What you'll build:** a model that guesses which of 3 kinds of iris flower you have from 4 measurements, and prints the exact yes/no questions it learned to ask.
**Time:** ~30 min · **Builds on:** [07 · Spam or not?](../07-spam-or-not) · **Needs:** nothing extra (the flower data comes with scikit-learn)

Like you're 10: it's a game of 20 Questions. "Are the petals thin?" "Yes." "Are they short?" "Yes." "Then it's a setosa!" The model works out which questions to ask by itself.

## Why this matters
Many real decisions must be **explainable**: a bank has to say why it refused a loan, a doctor wants to know why a tool flagged a patient. A **decision tree** is a model whose reasoning you can print and read. Trees (and "forests" of many trees) are also among the most-used models for spreadsheet-style data in industry. And this lesson shows a classic trap: a model that scores 100% on its examples isn't necessarily better.

## What you'll learn
- **Decision tree**: a model that learns a chain of yes/no questions about the features, ending in an answer.
- **Multi-class classification**: picking one of more than two categories (here 3 kinds of iris).
- **Built-in datasets**: `load_iris()` gives you 150 real flowers measured by a botanist, ready to use.
- **Tree depth**: how many questions in a row the tree may ask. More depth = more detailed rules.
- **Accuracy**: the share of flowers it labels correctly (`model.score`).

## Before you start
- Venv on, and this part's install line done (skip if done already):
  ```bash
  pip install scikit-learn joblib fastapi "uvicorn[standard]"
  ```
  This lesson uses `scikit-learn` only (version 1.3 or newer, which the line above gives you).
- No API key needed. No download: the iris data is stored inside scikit-learn.

## Run it
1. From the course folder (`ai-from-zero`):
   ```bash
   cd part-2-machine-learning/08-flower-guesser
   python flower_guesser.py
   ```
2. Now give your own 4 measurements in cm: sepal length, sepal width, petal length, petal width (the sepals are the small green leaves under the petals):
   ```bash
   python flower_guesser.py 5.0 3.4 1.5 0.2
   ```

### What you should see
```
The questions the model learned to ask (all sizes in cm):

|--- petal width <= 0.80
|   |--- class: setosa
|--- petal width >  0.80
|   |--- petal width <= 1.75
|   |   |--- petal length <= 4.95
|   |   |   |--- class: versicolor
|   |   |--- petal length >  4.95
|   |   |   |--- class: virginica
|   |--- petal width >  1.75
|   |   |--- petal length <= 4.85
|   |   |   |--- class: virginica
|   |   |--- petal length >  4.85
|   |   |   |--- class: virginica

It gets 97% of the 150 flowers right.

🌸 Measurements [5.9, 3.0, 5.1, 1.8] → it's an iris virginica
```
and for `5.0 3.4 1.5 0.2` the last line is:
```
🌸 Measurements [5.0, 3.4, 1.5, 0.2] → it's an iris setosa
```
**How to read the tree:** start at the top. Each `|---` line is a question; the lines indented under it are what happens if the answer is yes (`<=`) or no (`>`). Follow the branches until you reach a `class:` line: that's the answer. Notice the very first question alone separates every setosa from the rest, and the model never needed the sepal measurements at all.

## How it works
```
flower [5.9, 3.0, 5.1, 1.8]
   └─ petal width 1.8 <= 0.80?  no
        └─ petal width 1.8 <= 1.75?  no
             └─ petal length 5.1 <= 4.85?  no  ──▶ virginica
```
1. `flowers = load_iris()` loads the dataset. `flowers.data` is 150 rows of 4 measurements; `flowers.target` is the answer for each row as a number (0, 1 or 2); `flowers.target_names` is `['setosa', 'versicolor', 'virginica']`, the names for those numbers.
2. `names` gives the 4 measurements short labels for printing.
3. `DecisionTreeClassifier(max_depth=3, random_state=0)` makes an empty tree that may ask at most 3 questions in a row. `random_state=0` makes it build the same tree on every run (when two questions are equally good, it picks the same one each time).
4. `model.fit(flowers.data, flowers.target)` builds the tree. At each step it tries every measurement and every cut-off value, and picks the question that best separates the kinds of flower. Then it repeats for each branch.
5. `export_text(model, feature_names=names, class_names=...)` turns the learned tree into the readable text above.
6. `model.score(flowers.data, flowers.target)` is the accuracy: the share of the 150 flowers it labels correctly. These are the flowers it learned from, so it's an easy test (lesson 06 showed the fair way: a hidden test set; see **Try this** 3).
7. `sys.argv[1:]` holds the numbers you typed; if none, it uses an example flower. The `try`/`except` and the `len(measurements) != 4` check give friendly messages for bad input.
8. `model.predict([measurements])[0]` walks your flower down the tree and returns a number. `flowers.target_names[guess]` turns that number into a name.

## If something goes wrong
- **`TypeError: export_text() got an unexpected keyword argument 'class_names'`** → your scikit-learn is older than 1.3. Run `pip install --upgrade scikit-learn`.
- **`Please give exactly 4 numbers`** → you typed fewer or more than 4. Example: `python flower_guesser.py 6.0 2.7 4.2 1.3`.
- **`Please give numbers only`** → use a dot for decimals (`1.5`), not a comma (`1,5`).
- **A strange answer for strange numbers** (like `50 50 50 50`) → the tree always gives one of the 3 answers, even for impossible flowers. It only knows how to compare against its cut-offs.
- **`ModuleNotFoundError: No module named 'sklearn'`** → switch your venv on and run the pip line.

## Try this
1. Change `max_depth=3` to `1`, then `2`, then `5`. How many questions does it ask, and what accuracy does it print each time?
2. Follow the printed rules by hand for `6.0 2.7 4.2 1.3`. What does the tree say? Then run it and check.
3. Give it a fair exam. Make a new file `fair_test.py` that hides 30% of the flowers with `train_test_split` (like lesson 06), and compares depths 1, 2, 3 and 10 on the hidden flowers.

<details><summary>Hints and solutions</summary>

1. Depth 1: one question, **67%** (it can only split setosa from "the rest", so it can never say virginica). Depth 2: **96%**. Depth 3: **97%**. Depth 5: **100%**: the rules get long and very specific, so the tree has basically memorised these 150 flowers.
2. Petal width 1.3 ≤ 0.80? No. Petal width 1.3 ≤ 1.75? Yes. Petal length 4.2 ≤ 4.95? Yes → **versicolor**. The program agrees: `it's an iris versicolor`.
3. ```python
   from sklearn.datasets import load_iris
   from sklearn.model_selection import train_test_split
   from sklearn.tree import DecisionTreeClassifier

   flowers = load_iris()
   train_x, test_x, train_y, test_y = train_test_split(flowers.data, flowers.target, test_size=0.3, random_state=0)
   for depth in [1, 2, 3, 10]:
       model = DecisionTreeClassifier(max_depth=depth, random_state=0).fit(train_x, train_y)
       print(f"max_depth={depth}: studied flowers {model.score(train_x, train_y):.0%}, new flowers {model.score(test_x, test_y):.0%}")
   ```
   Output:
   ```
   max_depth=1: studied flowers 70%, new flowers 60%
   max_depth=2: studied flowers 96%, new flowers 91%
   max_depth=3: studied flowers 98%, new flowers 98%
   max_depth=10: studied flowers 100%, new flowers 98%
   ```
   Depth 10 is perfect on flowers it studied but no better than depth 3 on new ones. Extra questions just memorise; they don't add understanding.
</details>

## Check yourself
1. Why might a bank prefer a decision tree to a model whose reasoning it can't read?
2. What does `max_depth` control, and what goes wrong if it's too small?
3. The tree scores 100% on its own 150 flowers at depth 5. Why isn't that proof it's a great model?
4. Which single measurement does the tree check first, and what does that tell you about the flowers?

<details><summary>Answers</summary>

1. It can show exactly why each decision was made (which questions, which cut-offs), which customers, managers and regulators may require.
2. How many questions the tree may ask in a row. Too small (like 1) and it can't express enough rules to tell all 3 kinds apart.
3. Those are the flowers it learned from, so it may simply have memorised them. Only flowers it has never seen give an honest score.
4. Petal width. One question about it (≤ 0.8 cm) separates all setosas from the other two kinds, so petal width is the most useful measurement.
</details>

## Learn more (optional)
- scikit-learn's guide to decision trees: https://scikit-learn.org/stable/modules/tree.html
- The iris dataset's story: https://en.wikipedia.org/wiki/Iris_flower_data_set
- Video: search YouTube for "StatQuest decision trees".

## Next
→ [09 · Group customers](../09-group-customers)
