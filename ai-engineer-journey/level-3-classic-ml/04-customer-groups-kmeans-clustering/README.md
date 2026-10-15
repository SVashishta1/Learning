# 3.4 · Customer groups: k-means clustering

**What you'll build:** you give the computer 300 shoppers (age, income, spending, visits) with **no labels**, and it discovers natural groups on its own. You turn those groups into marketing personas. You also write k-means yourself in about 10 lines.
**Like you're 10:** dump a box of mixed LEGO on the floor and ask a friend to sort it into 4 piles *without telling them how*. They'll probably group by colour or size on their own. That's clustering.
**Time:** ~1 h · **Builds on:** [3.3 Iris flower classifier](../03-iris-flower-classifier-decision-tree) · **Needs:** nothing extra

## Why this matters
Most real data has no labels: nobody has written "bargain hunter" next to each customer. Clustering finds structure anyway. Companies use it for customer segmentation (who gets which offer), grouping similar products or documents, and spotting unusual behaviour (a customer who fits no group may be fraud). It's also a common first step to understand a new dataset.

## What you'll learn
- **Unsupervised learning**: finding structure in data that has no "right answers" attached.
- **The k-means loop**: pick centres → everyone joins the nearest centre → move each centre to the middle of its team → repeat.
- **The elbow method**: a simple way to choose how many groups (k) to ask for.
- **Scaling for distances**: why income in thousands mustn't drown out visits per month.
- **From clusters to actions**: a cluster is only useful once you describe it and decide what to do with it.

## Before you start
```bash
pip install -r requirements.txt
```
- `numpy`: arrays and the from-scratch k-means maths.
- `pandas`: the customer table and the per-group averages.
- `scikit-learn`: `StandardScaler` and the library `KMeans`.
- `matplotlib`: for the plotting exercise in "Try this".

No API key or internet needed: the customers are generated in the script.

## Run it
1. From the course root:
   ```bash
   cd level-3-classic-ml/04-customer-groups-kmeans-clustering
   pip install -r requirements.txt
   ```
2. Run it:
   ```bash
   python customer_groups.py
   ```

### What you should see
```
From-scratch cluster sizes: [74 75 75 76]

k | inertia
1 |  1200.0 ████████████████████████████████████████████████
2 |   670.0 ██████████████████████████
3 |   379.9 ███████████████
4 |   168.4 ██████
5 |   156.7 ██████
6 |   146.4 █████
7 |   138.4 █████
8 |   129.2 █████

Average customer in each group:
         age  income_k  spend_score  visits  customers
group
0      55.4      98.3         19.6     2.2         76
1      25.3      31.6         80.2    10.0         75
2      34.8      45.3         42.0     4.0         75
3      44.4     113.7         85.6     6.2         74

Suggested marketing per group:
  group 0: 🧐 Rich but careful: quality/value messaging
  group 1: 🎉 Young enthusiasts: social media + discounts
  group 2: 🛒 Budget regulars: loyalty points
  group 3: 💎 Big spenders: VIP program
```
What to look at:
- **Your from-scratch k-means** found 4 groups of about 75 people. The data was made from 4 hidden groups of exactly 75, so it got them almost perfectly.
- **The elbow**: inertia drops a lot from k=1 to k=4, then barely moves. That bend at 4 is the "elbow".
- **The averages table** describes each group in plain numbers. Group 0 is older, well-off, and spends little. That's a persona you can act on. (Group numbers are arbitrary; another run or version may number them differently.)

## How it works
1. **Making the shoppers.** `groups` lists 4 hidden "typical shoppers" as (age, income in $k, spending score 0–100, visits per month). For each one, `rng.normal(center, (5, 12, 10, 1.5))` creates 75 customers scattered around it. `np.clip(rows, 1, None)` stops anything going below 1. We pretend we don't know about these groups: the algorithm only sees the 300 rows.
2. **Scaling.** `StandardScaler().fit_transform(df)` turns each column into "standard deviations from average". k-means measures **distance**, and without scaling a $20k income difference (a "distance" of 20) would swamp a difference of 5 visits a month, even though both matter.
3. **`kmeans_from_scratch(X, k)`** (the numbered comments in the code match these steps):
   1. pick `k` random customers as the starting **centres** (also called *centroids*);
   2. `dists` = squared distance from every customer to every centre. `X[:, None, :] - centers[None]` uses NumPy *broadcasting* to make a 300 × 4 × 4 grid of differences in one line;
   3. `labels = dists.argmin(1)`: each customer joins their nearest centre's team;
   4. move each centre to the average position of its team (if a team is empty, the centre stays put).
   Repeat 20 times. The centres slide towards the middle of the real groups and stop moving.
   ```
   centres:   x        x               teams form          centres move to the middle
   customers: . . .  . . .    ──►   (. . .)(. . .)   ──►   (. x .)(. x .)   ──► repeat
   ```
4. **Elbow method.** For k = 1 to 8, scikit-learn's `KMeans(n_clusters=k, n_init=10)` is fitted and its **inertia** printed: the total squared distance from each customer to their centre. More groups *always* lowers inertia (with 300 groups it would be 0!), so you look for the k where adding another group stops helping much. `n_init=10` runs k-means 10 times from different random starts and keeps the best, because a bad start can give a bad result.
5. **Final model.** `KMeans(n_clusters=4)` labels every customer; `df["group"] = km.labels_` adds the label as a column. `df.groupby("group").mean()` then describes the average customer in each group, and `value_counts()` counts them.
6. **`persona(row)`** turns each group's averages into a business action with simple if-rules (high income + high spending → VIP program, and so on). This is the step that makes clustering useful: the algorithm finds groups; *you* name them and decide what to do.

## If something goes wrong
- **Different group numbers than the sample** (e.g. "big spenders" is group 1 instead of 3) → normal. Cluster numbers are just names; another scikit-learn version can number them differently. Check the averages, not the numbers.
- **The emoji show as boxes or `UnicodeEncodeError`** (older Windows terminals) → run `set PYTHONIOENCODING=utf-8` (or `$env:PYTHONIOENCODING="utf-8"` in PowerShell) before the script, or use Windows Terminal.
- **`ModuleNotFoundError`** → activate your virtual environment and run `pip install -r requirements.txt`.
- **A warning about memory leaks with KMeans on Windows** → harmless; you can silence it by setting the environment variable `OMP_NUM_THREADS=1`.

## Try this
1. **Wrong number of groups.** Change the final `KMeans(n_clusters=4, ...)` to 3 and then 6. Do the personas still make sense?
   <details><summary>Hint</summary>

   With k=3, the "rich but careful" and "budget regulars" groups get merged into one 142-person group with average income $74k, and it's labelled "Budget regulars", which fits neither. With k=6, two real groups get split in half, so you get two "Young enthusiasts" and two "Budget regulars" groups. Asking for the wrong k still gives an answer; it just isn't a useful one. That's why the elbow check matters.
   </details>
2. **See the groups.** Plot `income_k` against `spend_score`, coloured by group.
   <details><summary>Solution</summary>

   Add at the end of the script:
   ```python
   import matplotlib.pyplot as plt
   plt.scatter(df.income_k, df.spend_score, c=df.group, cmap="tab10")
   plt.xlabel("income ($k)"); plt.ylabel("spending score"); plt.title("Customer groups")
   plt.savefig("groups.png"); print("Saved groups.png")
   ```
   Open `groups.png`. You'll see 4 blobs, one colour each. Try other pairs of columns (e.g. `age` vs `visits`): some views separate the groups well, others mix them. k-means uses all 4 columns at once, which no single 2-D plot can show.
   </details>
3. **Let the algorithm choose k.** Try `DBSCAN`, which finds the number of groups by itself and labels outliers as `-1`.
   <details><summary>Solution</summary>

   Add at the end:
   ```python
   from sklearn.cluster import DBSCAN
   db = DBSCAN(eps=0.6, min_samples=5).fit(X)
   print("groups found:", len(set(db.labels_)) - (-1 in db.labels_), "| outliers:", (db.labels_ == -1).sum())
   ```
   With `eps=0.6` it finds 4 groups and 20 outliers. `eps` is "how close counts as a neighbour" (in scaled units). Try 0.5 (more outliers) and 0.8 (groups start merging, only 3 found).
   </details>

## Check yourself
1. What's the difference between this lesson and 3.3 (iris) in terms of the data you give the model?
2. Why do we scale the columns before k-means?
3. Inertia keeps falling as k grows. Why not just pick k = 8?
4. k-means put a customer in group 2. How would you explain to a marketing manager what that means?

<details><summary>Answers</summary>

1. In 3.3 every flower came with its species (labels), and the model learned to predict them: supervised learning. Here there are no labels; the model only finds groups of similar rows: unsupervised learning.
2. k-means uses distances. Without scaling, columns with big numbers (income) dominate the distance and columns with small numbers (visits) are basically ignored.
3. More groups always fit tighter, but beyond the elbow you're splitting real groups into pieces that aren't meaningfully different. You'd have 8 marketing campaigns for 4 kinds of people.
4. Use the averages table: "Group 2 are people in their mid-30s earning about $45k who spend moderately and visit about 4 times a month." Then describe the action you'd take for them.
</details>

## Learn more (optional)
- K-means clustering (StatQuest): https://www.youtube.com/results?search_query=statquest+k-means+clustering
- DBSCAN, Clearly Explained (StatQuest): https://www.youtube.com/results?search_query=statquest+dbscan
- scikit-learn clustering guide: https://scikit-learn.org/stable/modules/clustering.html

## Next
→ [3.5 · Model evaluation playground](../05-model-evaluation-playground)
