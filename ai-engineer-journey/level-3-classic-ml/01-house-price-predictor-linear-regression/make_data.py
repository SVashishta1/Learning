"""Creates houses.csv: 500 made-up houses whose prices follow a hidden rule (plus noise).
Because we KNOW the hidden rule, we can check whether the model rediscovers it."""
import numpy as np
import pandas as pd


def make_houses(n=500, seed=7):
    rng = np.random.default_rng(seed)
    size = rng.normal(140, 40, n).clip(40, 350)          # square metres
    bedrooms = np.clip(np.round(size / 40 + rng.normal(0, 0.7, n)), 1, 6)
    age = rng.uniform(0, 60, n)                           # years
    dist = rng.exponential(8, n).clip(0.5, 40)            # km to city centre
    # The hidden rule (in thousands of $):
    price = 50 + 2.5 * size + 10 * bedrooms - 1.2 * age - 4 * dist + rng.normal(0, 25, n)
    return pd.DataFrame({"size_m2": size.round(1), "bedrooms": bedrooms.astype(int), "age_years": age.round(1),
                         "km_to_center": dist.round(1), "price_k": price.round(1)})


if __name__ == "__main__":
    make_houses().to_csv("houses.csv", index=False)
    print("wrote houses.csv")
