"""Project 3.4: find customer groups with k-means. No labels given; the algorithm discovers the groups.
Step 1 writes k-means from scratch (15 lines). Step 2 uses scikit-learn and turns clusters into marketing personas."""
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

rng = np.random.default_rng(3)
# A made-up mall: 4 hidden kinds of shoppers (we pretend we don't know this!)
groups = [  # (age, income $k, spending score 0-100, visits/month)
    (25, 30, 80, 10), (45, 110, 85, 6), (55, 100, 20, 2), (35, 45, 40, 4)]
rows = [rng.normal(center, (5, 12, 10, 1.5)) for center in groups for _ in range(75)]
df = pd.DataFrame(np.clip(rows, 1, None), columns=["age", "income_k", "spend_score", "visits"]).round(1)


def kmeans_from_scratch(X, k, steps=20, seed=0):
    r = np.random.default_rng(seed)
    centers = X[r.choice(len(X), k, replace=False)]           # 1. pick k random customers as starting centers
    for _ in range(steps):
        dists = ((X[:, None, :] - centers[None]) ** 2).sum(-1)  # 2. distance from every point to every center
        labels = dists.argmin(1)                                 # 3. join the nearest center's team
        centers = np.array([X[labels == j].mean(0) if (labels == j).any() else centers[j] for j in range(k)])  # 4. move centers
    return labels, centers


X = StandardScaler().fit_transform(df)   # scale so income (~100) doesn't drown out visits (~5)
labels, _ = kmeans_from_scratch(X, 4)
print("From-scratch cluster sizes:", np.bincount(labels))

# Elbow method: how many groups? Inertia = total distance to centers. Look for the "elbow" where it stops dropping fast.
print("\nk | inertia")
for k in range(1, 9):
    inertia = KMeans(n_clusters=k, n_init=10, random_state=0).fit(X).inertia_
    print(f"{k} | {inertia:7.1f} {'█' * int(inertia / 25)}")

km = KMeans(n_clusters=4, n_init=10, random_state=0).fit(X)
df["group"] = km.labels_
summary = df.groupby("group").mean().round(1)
summary["customers"] = df.group.value_counts().sort_index()
print("\nAverage customer in each group:\n", summary)


def persona(row):
    if row.income_k > 80 and row.spend_score > 60: return "💎 Big spenders: VIP program"
    if row.income_k > 80: return "🧐 Rich but careful: quality/value messaging"
    if row.spend_score > 60: return "🎉 Young enthusiasts: social media + discounts"
    return "🛒 Budget regulars: loyalty points"


print("\nSuggested marketing per group:")
for g, row in summary.iterrows():
    print(f"  group {g}: {persona(row)}")
