# 09 · Group customers

**What you'll build:** you give the computer 150 shoppers with **no labels at all**, and it discovers by itself that they fall into 3 groups (students, high earners, retirees).
**Time:** ~30 min · **Builds on:** [08 · Flower guesser](../08-flower-guesser) · **Needs:** nothing extra

Like you're 10: tip a box of mixed sweets onto the table and sort them into piles that look alike, without anyone telling you the names of the sweets. That's what the computer does here.

## Why this matters
In lessons 06–08 every example came with the right answer (a price, "spam", a flower name). That's **supervised learning**. Often nobody has labelled the data, and you still want to find structure in it: shops group customers to send them different offers, streaming services group viewers with similar taste, banks spot unusual transactions that fit no group. This is **unsupervised learning**, and k-means is its most famous tool.

## What you'll learn
- **Unsupervised learning**: finding patterns in data that has no answers attached.
- **Clustering**: putting similar items into groups ("clusters").
- **k-means**: a clustering method that places k group centres and moves them until each sits in the middle of its group.
- **Scaling**: putting features on the same scale so a big-number feature (spending in $) doesn't drown out a small-number one (age).
- **Pipeline** (again): scaling and clustering glued into one model.

## Before you start
- Venv on, and this part's install line done (skip if done already):
  ```bash
  pip install scikit-learn joblib fastapi "uvicorn[standard]"
  ```
  This lesson uses `scikit-learn` only.
- No API key needed.

## Run it
1. From the course folder (`ai-from-zero`):
   ```bash
   cd part-2-machine-learning/09-group-customers
   python group_customers.py
   ```

### What you should see
```
Group 0: 50 shoppers, average age 45, spends $881/month
Group 1: 50 shoppers, average age 68, spends $151/month
Group 2: 50 shoppers, average age 22, spends $283/month

A new shopper (age 30, spends $850) belongs to group 0
```
The code made 50 students (around age 22, $300/month), 50 high earners (around 45, $900) and 50 retirees (around 68, $150), then threw the labels away. The model found **exactly 50 / 50 / 50**, with averages very close to the hidden ones. It doesn't know the words "student" or "retiree"; it just numbers the groups 0, 1, 2. You give them names. The new 30-year-old who spends $850 lands with the high earners because of their spending.

## How it works
```
150 shoppers [age, spend] ──StandardScaler──▶ same-scale numbers ──KMeans(3)──▶ group 0 / 1 / 2 for each shopper
```
k-means itself, step by step:
```
1. drop 3 group centres somewhere
2. every shopper joins the nearest centre
3. every centre moves to the middle of its shoppers
4. repeat 2–3 until nothing changes
```
1. **Make the shoppers.** `random.gauss(22, 3)` picks a number around 22, usually within about ±3 (a "bell curve"). Three loops make 50 shoppers each, every one stored as `[age, money spent per month]`. `random.seed(3)` keeps the numbers the same on every run.
2. `n_groups = 3` is how many groups to look for. k-means can't decide this by itself; you choose the "k".
3. **Scale.** `StandardScaler()` rescales each feature so its average is 0 and its typical spread is 1. Without it, a $100 difference in spending would count 100 times more than a 1-year difference in age, just because the numbers are bigger.
4. **Cluster.** `KMeans(n_clusters=n_groups, n_init=10, random_state=0)` runs the 4 steps above. `n_init=10` runs the whole thing 10 times from different starting centres and keeps the best result (a bad start can give odd groups). `random_state=0` makes it repeatable.
5. `model.fit_predict(shoppers)` does both at once: learns the groups and returns a group number for every shopper. Note there are no answers passed in, only `shoppers`. That's what makes it unsupervised.
6. **Describe each group.** The loop over `range(n_groups)` picks the shoppers in that group (`zip(shoppers, groups)` pairs each shopper with its number), then averages their age and spending.
7. **New shopper.** `model.predict([new_shopper])[0]` scales the new shopper the same way and finds the nearest group centre.

## If something goes wrong
- **`ModuleNotFoundError: No module named 'sklearn'`** → switch your venv on and run the pip line.
- **Your group numbers are in a different order** → the numbers are just name tags. If you change the data or `random_state`, the "high earners" might become group 2. Look at the averages, not the numbers.
- **`ZeroDivisionError: division by zero`** → a group ended up with no members, usually because you changed the loop to `range(...)` with a different number than `n_clusters`. Use the `n_groups` variable for both, as the code does.
- **The groups look mixed up** → check that `StandardScaler()` is still in the pipeline, and that `n_groups` matches the number of real groups (see **Try this**).

## Try this
1. Change `n_groups = 3` to `2`, then to `5`. Do the groups still make sense?
2. Remove `StandardScaler()` from the pipeline, so it reads `make_pipeline(KMeans(...))`. What happens to the groups?
3. Give each group a marketing name and an offer, the way a real shop would, and print the offer for 3 new shoppers.

<details><summary>Hints and solutions</summary>

1. With 2 groups, students and high earners are merged into one group of 100 (average age 33, $582/month): the model had to put them somewhere. With 5, real groups get split into smaller ones (e.g. high earners into $989 and $809 spenders). Choosing k well is part of the job; you try a few values and pick the one that makes sense.
2. You get 50 / 59 / 41 shoppers instead of 50 / 50 / 50: some older students and younger retirees swap groups, because age now barely matters next to spending. Scaling matters.
3. The group numbers match the output above (0 = high earners, 1 = retirees, 2 = students). Add to the end of the file:
   ```python
   group_names = {0: "Big spenders", 1: "Silver savers", 2: "Young fun-seekers"}
   offers = {0: "free premium delivery", 1: "a loyalty discount on essentials", 2: "2-for-1 cinema tickets"}
   for shopper in [[30, 850], [70, 120], [19, 350]]:
       group = model.predict([shopper])[0]
       print(f"Age {shopper[0]}, spends ${shopper[1]}: {group_names[group]} → offer {offers[group]}")
   ```
   Output:
   ```
   Age 30, spends $850: Big spenders → offer free premium delivery
   Age 70, spends $120: Silver savers → offer a loyalty discount on essentials
   Age 19, spends $350: Young fun-seekers → offer 2-for-1 cinema tickets
   ```
</details>

## Check yourself
1. What's the key difference between this lesson and lessons 06–08?
2. Why do we scale age and spending before clustering?
3. The model says "group 2". Why can't it say "students"?
4. Who decides how many groups k-means looks for, and how could you pick a good number?

<details><summary>Answers</summary>

1. Here the examples have no answers (labels). The model has to find the structure on its own: unsupervised learning.
2. k-means measures distance between shoppers. Without scaling, spending (hundreds of dollars) dominates the distance and age (tens of years) barely counts.
3. It never saw the word "student". It only knows these shoppers are close to each other. A human looks at each group's averages and names it.
4. You do, with `n_clusters`. Try several values, look at whether the groups are meaningful and useful, and pick the simplest one that makes sense (there are also scoring methods, like the "elbow method", for help).
</details>

## Learn more (optional)
- scikit-learn's guide to clustering (with pictures of k-means): https://scikit-learn.org/stable/modules/clustering.html
- Video: search YouTube for "StatQuest k-means clustering".

## Next
→ [10 · Save a model and serve it as an API](../10-save-a-model-and-serve-it)
