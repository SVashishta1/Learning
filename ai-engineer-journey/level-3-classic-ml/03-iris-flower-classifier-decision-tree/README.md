# 3.3 · Iris flower classifier: a decision tree

**What you'll build:** a model that names an iris flower's species from 4 measurements, and prints its reasoning as **if/else rules** (plus a picture of the tree).
**Like you're 10:** the game "20 Questions". "Is the petal narrower than 0.7 cm?" Yes → setosa! No → ask another question. The tree learns the *best* questions to ask, in the best order.
**Time:** ~45 min · **Builds on:** [3.2 Spam detector](../02-spam-detector-logistic-regression) · **Needs:** nothing extra (the dataset is built into scikit-learn)

## Why this matters
Decision trees are the model you can hand to a non-programmer: every prediction is a short chain of yes/no questions. On their own they're used where decisions must be explained (loan approvals, medical triage checklists). Combined into **random forests** and **gradient boosting** (XGBoost, LightGBM), trees are the top choice for spreadsheet-style data in industry and win most tabular-data competitions.

## What you'll learn
- **Decision tree**: a flowchart of yes/no questions learned from data.
- **Splits and Gini impurity**: how the tree picks the question that best separates the classes.
- **Feature importance**: which measurements the tree actually relied on.
- **Depth and overfitting**: deeper trees can memorise the training data; always compare train vs test accuracy.

## Before you start
```bash
pip install -r requirements.txt
```
- `scikit-learn`: the iris dataset, the decision tree and the plotting helper.
- `matplotlib`: draws the tree as a picture (`iris_tree.png`). If it's missing, the script still runs and just skips the picture.

No API key or internet needed.

## Run it
1. From the course root:
   ```bash
   cd level-3-classic-ml/03-iris-flower-classifier-decision-tree
   pip install -r requirements.txt
   ```
2. Run it:
   ```bash
   python iris_tree.py
   ```
3. Open `iris_tree.png` (created in the same folder) to see the tree drawn as a flowchart.

### What you should see
```
Test accuracy: 93.3%

The rules the tree learned (read top to bottom):
|--- petal width (cm) <= 0.70
|   |--- class: 0
|--- petal width (cm) >  0.70
|   |--- petal width (cm) <= 1.55
|   |   |--- petal length (cm) <= 4.95
|   |   |   |--- class: 1
|   |   |--- petal length (cm) >  4.95
|   |   |   |--- class: 2
|   |--- petal width (cm) >  1.55
|   |   |--- petal length (cm) <= 4.85
|   |   |   |--- class: 1
|   |   |--- petal length (cm) >  4.85
|   |   |   |--- class: 2

Which measurements mattered most:
  petal width (cm)     ██████████████████████████████████████ 0.96
  petal length (cm)    █ 0.04
  sepal length (cm)     0.00
  sepal width (cm)      0.00

depth | train acc | test acc
1     |     66.7% |    66.7%
2     |     97.1% |    88.9%
3     |     98.1% |    93.3%
5     |    100.0% |    97.8%
10    |    100.0% |    97.8%
None  |    100.0% |    97.8%

My flower [5.9, 3.0, 5.1, 1.8] is a: virginica
Saved iris_tree.png
```
What to look at:
- **The rules**: class 0 = setosa, 1 = versicolor, 2 = virginica. The very first question ("petal width ≤ 0.70?") separates all setosa flowers on its own.
- **Importance**: the tree only used petal measurements. Sepal measurements scored 0.00, so they were never asked about.
- **The depth table**: depth 1 can only ask one question, so it can only separate 2 of the 3 species (66.7%). From depth 5, the tree is 100% right on training data.

## How it works
1. **`load_iris()`** loads a famous dataset from 1936: 150 iris flowers, 4 measurements each (sepal length, sepal width, petal length, petal width, in cm), 3 species, 50 of each. It ships inside scikit-learn, so no download.
2. **`train_test_split(..., test_size=0.3, stratify=iris.target)`** keeps 45 flowers for testing, with the same 1/3–1/3–1/3 species mix.
3. **`DecisionTreeClassifier(max_depth=3)`** builds the tree. At each step it tries every measurement and every cut-off value, and keeps the question that makes the two resulting groups as **pure** as possible. Purity is measured by **Gini impurity**: 0 means "everyone in this group is the same species", higher means "mixed". `max_depth=3` stops after 3 levels of questions. `random_state=0` makes the result the same every run.
4. **`export_text(...)`** prints the learned questions as indented if/else rules. Each `|---` is one question; `class: N` is the answer at the end of a branch (a **leaf**).
5. **`tree.feature_importances_`** says how much each measurement helped reduce impurity across the whole tree (they add up to 1.0). The `█` bar is just that number × 40.
6. **The depth experiment** trains trees of depth 1, 2, 3, 5, 10 and unlimited (`None`) and prints training vs test accuracy. Deeper trees can keep asking questions until every training flower is in its own pure leaf, so training accuracy hits 100%. Iris is tiny and clean, so test accuracy holds up here. On noisy real data, an unlimited tree memorises the noise and test accuracy drops (you'll see this in 3.5). The habit to build: **always compare train vs test**.
7. **`tree.predict(flower)`** walks your flower down the tree: petal width 1.8 > 0.70 → > 1.55 → petal length 5.1 > 4.85 → class 2, virginica.
8. **`plot_tree(...)`** draws the same tree with matplotlib. Each box shows the question, the Gini score, how many training flowers reached it (`samples`), how many of each species (`value`), and the majority species. Colour shows the majority species; paler = more mixed.

## If something goes wrong
- **No `iris_tree.png` appears** → matplotlib isn't installed (the script silently skips the picture). Run `pip install matplotlib`. Also check you're looking in the folder you ran the script from.
- **`ValueError: X has 4 features, but ... is expecting 2 features`** (after editing) → your `flower` must have the same number of measurements as the data you trained on.
- **`AttributeError: 'RandomForestClassifier' object has no attribute 'tree_'`** → `export_text` and `plot_tree` only work on a single tree, not a forest. See exercise 1's solution.
- **Numbers differ slightly from the sample** → a different scikit-learn version can break ties between equally good splits differently. The overall picture stays the same.

## Try this
1. **A forest of trees.** Compare your tree with `RandomForestClassifier(n_estimators=100)`: 100 trees, each trained on a random sample, voting together. Better or the same here?
   <details><summary>Solution</summary>

   Add this at the end of `iris_tree.py` (so the tree-drawing code still uses your single tree):
   ```python
   from sklearn.ensemble import RandomForestClassifier
   forest = RandomForestClassifier(n_estimators=100, random_state=0).fit(X_train, y_train)
   print(f"Forest test accuracy: {forest.score(X_test, y_test):.1%}")
   print("Forest importances:", dict(zip(iris.feature_names, forest.feature_importances_.round(2))))
   ```
   You get 88.9%, slightly *worse* than the depth-3 tree's 93.3%. With 45 test flowers, one or two flowers make the difference. Forests shine on bigger, noisier data. Notice the forest spreads importance over petal length and width (0.45 / 0.43) instead of relying on one feature.
   </details>
2. **Sepals only.** Train using only the two *sepal* measurements. How much worse is it, and why?
   <details><summary>Hint</summary>

   Right after `iris = load_iris()` add:
   `iris.data, iris.feature_names = iris.data[:, :2], iris.feature_names[:2]`
   and change the flower to `flower = [[5.9, 3.0]]`. Test accuracy falls to 73.3%. The importances in the main run already told you why: sepals barely separate the species; petals do almost all the work.
   </details>
3. **A different dataset.** Replace `load_iris` with `load_wine` (178 wines, 13 chemical measurements, 3 grape types). What does the tree ask about now?
   <details><summary>Hint</summary>

   Change both `load_iris` words (import and call). The `flower` has 4 numbers but wines have 13, so change that line to `flower = [list(iris.data[0])]` (the first wine) or delete the last two "My flower" lines. Test accuracy is about 98%. Read the rules to see which chemicals the tree picked.
   </details>

## Check yourself
1. What does a Gini impurity of 0 mean for a group of flowers?
2. Why did the depth-1 tree get exactly 66.7%?
3. A tree scores 100% on training data and 70% on test data. What's happening, and what's one fix?
4. Why might a bank prefer a small decision tree over a neural network for loan decisions?

<details><summary>Answers</summary>

1. Every flower in the group is the same species: the group is perfectly pure.
2. With one question it can only split the flowers into two groups, so it can name at most 2 of the 3 species correctly. Each species is one third of the data, so it gets 2/3 right.
3. It's overfitting: memorising training data (including noise) instead of learning general rules. Limit `max_depth` (or require a minimum number of samples per leaf), or use a forest.
4. They must explain each decision to customers and regulators. A tree's rules can be read and checked by a person; a neural network's millions of weights can't.
</details>

## Learn more (optional)
- Decision and Classification Trees, Clearly Explained (StatQuest): https://www.youtube.com/results?search_query=statquest+decision+and+classification+trees+clearly+explained
- Random Forests (StatQuest): https://www.youtube.com/results?search_query=statquest+random+forests+part+1
- scikit-learn decision trees guide: https://scikit-learn.org/stable/modules/tree.html

## Next
→ [3.4 · Customer groups: k-means clustering](../04-customer-groups-kmeans-clustering)
