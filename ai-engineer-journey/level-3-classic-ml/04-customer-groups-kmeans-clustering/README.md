# 3.4 · Customer groups: k-means clustering

**What you build:** you give the computer 300 shoppers (age, income, spending, visits) with **no labels**, and it discovers natural groups. You turn those into marketing personas. You also write k-means yourself in 15 lines.
**Like you're 10:** dump a box of mixed LEGO on the floor and ask a friend to sort it into 4 piles *without telling them how*. They'll probably group by colour or size on their own. That's clustering.

## Run it
```bash
cd level-3-classic-ml/04-customer-groups-kmeans-clustering
pip install -r requirements.txt
python customer_groups.py
```

## Key ideas
- **Unsupervised learning:** no right answers to learn from, only structure to find.
- **k-means loop:** pick k centers → everyone joins the nearest center → move each center to the middle of its team → repeat.
- **Elbow method:** more groups always lower the inertia. Pick the k where adding another group stops helping much (here, 4).
- **Scaling matters:** without `StandardScaler`, income (big numbers) would dominate distance.
- **Business value:** clusters are only useful once you *name* them and decide an *action* per group.

## Your turn
1. Run k-means with k = 3 and k = 6. Do the personas still make sense?
2. Plot `income_k` vs `spend_score` coloured by group with matplotlib.
3. Try `DBSCAN` from sklearn, which finds the number of groups by itself and flags outliers.

## Watch
- K-means clustering (StatQuest): https://www.youtube.com/results?search_query=statquest+k-means+clustering
