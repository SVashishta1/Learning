# Find natural groups of shoppers WITHOUT telling the computer what the groups are.
import random

from sklearn.cluster import KMeans
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

random.seed(3)
shoppers = []        # each shopper: [age, money spent per month]
for _ in range(50):
    shoppers.append([random.gauss(22, 3), random.gauss(300, 60)])    # students who spend a lot on fun
for _ in range(50):
    shoppers.append([random.gauss(45, 6), random.gauss(900, 120)])   # high earners
for _ in range(50):
    shoppers.append([random.gauss(68, 5), random.gauss(150, 40)])    # careful retirees

# StandardScaler puts age (20-70) and spending (100-1000) on the same scale, so spending doesn't drown out age.
model = make_pipeline(StandardScaler(), KMeans(n_clusters=3, n_init=10, random_state=0))   # "please find 3 groups"
groups = model.fit_predict(shoppers)

for group in range(3):
    members = [s for s, g in zip(shoppers, groups) if g == group]
    avg_age = sum(m[0] for m in members) / len(members)
    avg_spend = sum(m[1] for m in members) / len(members)
    print(f"Group {group}: {len(members)} shoppers, average age {avg_age:.0f}, spends ${avg_spend:.0f}/month")

new_shopper = [30, 850]
print(f"\nA new shopper (age 30, spends $850) belongs to group {model.predict([new_shopper])[0]}")
