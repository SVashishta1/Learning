# Step 1: train the house-price model once and SAVE it to a file. Same made-up houses as project 06.
import random
from pathlib import Path

import joblib
from sklearn.linear_model import LinearRegression

random.seed(1)
houses, prices = [], []
for _ in range(500):
    size, bedrooms, km = random.randint(40, 250), random.randint(1, 5), random.randint(1, 30)
    houses.append([size, bedrooms, km])
    prices.append(50_000 + 2_500 * size + 10_000 * bedrooms - 4_000 * km + random.randint(-20_000, 20_000))

model = LinearRegression().fit(houses, prices)

model_file = Path(__file__).parent / "house_model.joblib"     # save it next to this file
joblib.dump(model, model_file)          # the trained "brain", saved like any other file
print(f"Saved {model_file.name}. Now run: uvicorn api:app --reload")
