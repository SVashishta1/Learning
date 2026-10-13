# 09 · Group customers

**What it does:** you give it 150 shoppers with no labels, and it discovers on its own that they fall into 3 groups (students, high earners, retirees).

## Run it
```bash
cd part-2-machine-learning/09-group-customers
python group_customers.py
```

## The idea in one sentence
**k-means** puts every shopper next to the nearest of k "group centres", then moves each centre to the middle of its group, and repeats until nothing changes.

## Try this
1. Change `n_clusters=3` to `2` and to `5`. Do the groups still make sense?
2. Remove `StandardScaler()` from the pipeline. The groups get worse because spending (big numbers) now matters far more than age.
3. Give each group a marketing name and a different offer, the way a real shop would.
