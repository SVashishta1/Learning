# 3.3 · Iris flower classifier: a decision tree

**What you build:** a model that names an iris flower's species from 4 measurements, and prints its reasoning as **if/else rules**.
**Like you're 10:** the game "20 Questions". "Is the petal shorter than 2.5 cm?" Yes → setosa! No → ask another question. The tree learns the *best* questions to ask, in the best order.

## Run it
```bash
cd level-3-classic-ml/03-iris-flower-classifier-decision-tree
pip install -r requirements.txt
python iris_tree.py
```
Open `iris_tree.png` to see the tree drawn as a flowchart.

## Key ideas
- **Splits:** at each step the tree picks the question that best separates the classes (measured by *Gini impurity*).
- **Explainable:** you can hand the printed rules to a botanist (or a bank regulator). Neural networks can't do this.
- **Depth vs. memorising:** in the depth table, deeper trees hit 100% on *training* data. Iris is tiny and clean, so test accuracy holds up here. On noisy real-world data, unlimited depth overfits badly (you'll see it clearly in 3.5). Always compare train vs. test.
- **Random forests** (many trees voting) and **XGBoost** (trees fixing each other's mistakes) are the go-to models for spreadsheet-style data in industry.

## Your turn
1. Replace the tree with `RandomForestClassifier(n_estimators=100)`. Better or the same?
2. Use only the two *sepal* features. How much worse is it, and why? (Look at feature importances.)
3. Try `load_wine()` instead of `load_iris()`; the rest of the code works unchanged.

## Watch
- Decision and Classification Trees, Clearly Explained (StatQuest): https://www.youtube.com/results?search_query=statquest+decision+and+classification+trees+clearly+explained
- Random Forests (StatQuest): https://www.youtube.com/results?search_query=statquest+random+forests+part+1
