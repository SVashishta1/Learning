"""Project 3.1: predict house prices. First from scratch (gradient descent), then with scikit-learn."""
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, r2_score, root_mean_squared_error
from sklearn.model_selection import train_test_split

from make_data import make_houses

df = make_houses()
features = ["size_m2", "bedrooms", "age_years", "km_to_center"]
X, y = df[features].to_numpy(), df["price_k"].to_numpy()
print(df.head(), "\n")

# Hold back 20% of houses the model NEVER sees during training: the honest exam.
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=0)

# ---------- A. From scratch: the one-neuron learner from 2.1, now with 4 inputs ----------
# Feature scaling: size (~140) and bedrooms (~3) live on very different scales, which makes
# gradient descent zig-zag. Standardise every column to mean 0, std 1.
mean, std = X_train.mean(0), X_train.std(0)
Xs_train, Xs_test = (X_train - mean) / std, (X_test - mean) / std

w, b, lr = np.zeros(len(features)), 0.0, 0.1   # one weight per feature, all starting at 0
for step in range(500):
    pred = Xs_train @ w + b
    err = pred - y_train
    w -= lr * 2 * Xs_train.T @ err / len(err)
    b -= lr * 2 * err.mean()
scratch_pred = Xs_test @ w + b
print(f"[from scratch] MAE on unseen houses: ${mean_absolute_error(y_test, scratch_pred):.1f}k")

# ---------- B. scikit-learn: same model, 2 lines ----------
model = LinearRegression().fit(X_train, y_train)
pred = model.predict(X_test)
print(f"[scikit-learn] MAE ${mean_absolute_error(y_test, pred):.1f}k | RMSE ${root_mean_squared_error(y_test, pred):.1f}k | R² {r2_score(y_test, pred):.3f}")

print("\nWhat the model learned (thousands of $ per unit) vs the hidden truth:")
hidden_truth = {"size_m2": 2.5, "bedrooms": 10, "age_years": -1.2, "km_to_center": -4}   # the rule in make_data.py
for name, coef in zip(features, model.coef_):
    print(f"  {name:13s} {coef:+7.2f}   (truth {hidden_truth.get(name, 0):+})")

# Our from-scratch weights are on the scaled features; convert back to compare
print("from-scratch, unscaled:", np.round(w / std, 2))

house = [[120, 3, 10, 5]]
print(f"\nA 120 m², 3-bed, 10-year-old house 5 km from the centre: ${model.predict(house)[0]:.0f}k")
