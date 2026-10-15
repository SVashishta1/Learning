# 3.1 · House price predictor: linear regression

**What you'll build:** a model that predicts a house's price from its size, bedrooms, age and distance to the city centre. You build it twice: first **from scratch** with the gradient descent you wrote in Level 2, then in 2 lines with scikit-learn.
**Like you're 10:** a real-estate agent learns rules like "+$2,500 per square metre, –$4,000 per km from the centre". Linear regression finds those numbers for you.
**Time:** ~1 h · **Builds on:** [2.1 One neuron learns y = 2x](../../level-2-neural-nets-from-scratch/01-one-neuron-learns-y-equals-2x) and [2.6 Micrograd](../../level-2-neural-nets-from-scratch/06-micrograd-autograd-engine) · **Needs:** nothing extra (no GPU, no API key)

## Why this matters
Linear regression is the first model data scientists reach for when the answer is a number: house prices, delivery times, sales next month, insurance costs. It trains in milliseconds, and every learned number is a rule a human can read and check. Banks, governments and insurers often *require* models they can explain like this.

## What you'll learn
- **Regression**: predicting a number (a price) rather than a category (spam / not spam).
- **Train/test split**: hide some data from the model during training so you can grade it honestly afterwards.
- **Feature scaling**: putting every column on a similar scale so gradient descent doesn't zig-zag.
- **Metrics (MAE, RMSE, R²)**: three ways to say how wrong the predictions are.
- **Coefficients**: the "rules" the model learned, one number per input column.

## Before you start
```bash
pip install -r requirements.txt
```
- `numpy`: fast maths on arrays (the from-scratch version).
- `pandas`: tables of data (the made-up houses).
- `scikit-learn`: ready-made ML models and metrics (version 1.4 or newer, for `root_mean_squared_error`).

No API key needed. No internet needed: the data is generated on your computer.

## Run it
1. From the course root, go into the project folder:
   ```bash
   cd level-3-classic-ml/01-house-price-predictor-linear-regression
   ```
2. Install the packages (once): `pip install -r requirements.txt`
3. Run the lesson:
   ```bash
   python house_prices.py
   ```
4. Optional: save the made-up data as a spreadsheet you can open in Excel or Google Sheets:
   ```bash
   python make_data.py      # writes houses.csv
   ```

### What you should see
```
   size_m2  bedrooms  age_years  km_to_center  price_k
0    140.0         3       39.9           0.5    327.9
1    151.9         3       17.4           1.7    415.6
2    129.0         3       23.9          26.7    269.8
3    104.4         4       27.8           7.9    254.5
4    121.8         4       54.3           3.2    295.0

[from scratch] MAE on unseen houses: $20.6k
[scikit-learn] MAE $20.6k | RMSE $25.8k | R² 0.942

What the model learned (thousands of $ per unit) vs the hidden truth:
  size_m2         +2.54   (truth +2.5)
  bedrooms        +7.65   (truth +10)
  age_years       -1.36   (truth -1.2)
  km_to_center    -4.02   (truth -4)
from-scratch, unscaled: [ 2.54  7.65 -1.36 -4.02]

A 120 m², 3-bed, 10-year-old house 5 km from the centre: $352k
```
What to look at:
- **Both versions get the same MAE ($20.6k).** Your hand-written gradient descent found the same answer as the library.
- **The learned numbers are close to the hidden truth.** The model rediscovered the rule just by looking at examples. (Bedrooms is the least accurate because bedrooms and size move together: big houses have more bedrooms, so the model can't fully tell their effects apart.)
- **R² 0.942** means the model explains about 94% of why prices differ. The rest is the random noise added on purpose.

## How it works
The flow:
```
make_houses() ──► table of 500 houses ──► split 80% train / 20% test
                                              │
                    ┌─────────────────────────┴─────────────────────────┐
           A. from scratch (gradient descent)               B. scikit-learn LinearRegression
                    └─────────────────────────┬─────────────────────────┘
                                   grade both on the 20% test houses
```

1. **`make_data.py` → `make_houses()`** invents 500 houses. Size, bedrooms, age and distance are random, and the price follows a **hidden rule**: `50 + 2.5×size + 10×bedrooms − 1.2×age − 4×distance + noise` (in thousands of $). Because you know the rule, you can check whether the model finds it. Real data never tells you the true rule, which is why this is a great first exercise.
2. **`X, y`**: `X` is the input table (4 columns, called *features*), `y` is the answer we want to predict (`price_k`).
3. **`train_test_split(..., test_size=0.2)`** hides 20% of the houses. The model never sees them during training, so they act as an honest exam. Grading a model on its own training data is like grading a student on questions they've already seen the answers to.
4. **Feature scaling.** Size is around 140, bedrooms around 3. With such different scales, one learning rate is too big for one column and too small for another, and gradient descent zig-zags. `(X_train - mean) / std` turns every column into "how many standard deviations from average", so they're all roughly −2 to +2. Note the mean and std come from the **training** set only (the test set stays truly unseen).
5. **The from-scratch loop** is your neuron from 2.1 with 4 inputs instead of 1. `w` holds one weight per feature, all starting at 0. For 500 steps it predicts (`Xs_train @ w + b`), measures the error, and nudges each weight `w` and the bias `b` downhill. `2 * Xs_train.T @ err / len(err)` is the gradient of the mean squared error, worked out for all 4 weights at once.
6. **scikit-learn's `LinearRegression().fit(...)`** solves the same problem directly with linear algebra (no loop, no learning rate). It doesn't need scaling because it doesn't use gradient descent.
7. **Metrics:**
   - **MAE** (mean absolute error) = the average miss in dollars. Easy to explain to a boss.
   - **RMSE** (root mean squared error) = like MAE, but big misses count extra. If RMSE is much bigger than MAE, you have a few terrible predictions.
   - **R²** = the share of price differences the model explains. 1.0 is perfect, 0 means "no better than always guessing the average price".
8. **Coefficients.** `model.coef_` holds one number per feature: "each extra m² adds $2.54k". The `hidden_truth` dictionary holds the real rule from `make_data.py` so you can compare. The from-scratch weights were learned on *scaled* features, so `w / std` converts them back to "per m²" units, and they match.
9. **Prediction.** `model.predict([[120, 3, 10, 5]])` plugs a new house into the learned rule.

## If something goes wrong
- **`ModuleNotFoundError: No module named 'sklearn'`** → the package is called `scikit-learn` when you install it: `pip install -r requirements.txt` (with your virtual environment activated).
- **`ImportError: cannot import name 'root_mean_squared_error'`** → your scikit-learn is older than 1.4. Run `pip install -U scikit-learn`.
- **`ModuleNotFoundError: No module named 'make_data'`** → you're running from the wrong folder. `cd` into the project folder first, then `python house_prices.py`.
- **From-scratch MAE is huge or `nan`** (after you edited the code) → the learning rate `lr` is too big or you removed the scaling step. Put scaling back, or try `lr = 0.01`.

## Try this
1. **Drop a feature.** Remove `"km_to_center"` from `features`, and change the example house at the bottom to `house = [[120, 3, 10]]` (it now has 3 numbers). How much worse does MAE get?
   <details><summary>Hint</summary>

   MAE jumps from about $20.6k to about $33.5k, and R² drops from 0.94 to 0.83. Distance really does affect price in the hidden rule, so without it the model can't explain those differences. Look at `bedrooms` too: it changes a lot, because the model now uses the remaining columns to "soak up" what's missing.
   </details>
2. **Add a curve.** Right after `df = make_houses()`, add `df["size_sq"] = df["size_m2"] ** 2`, add `"size_sq"` to `features`, and change the example house to `house = [[120, 3, 10, 5, 120 ** 2]]`. Does it help? Why not, given the hidden rule?
   <details><summary>Hint</summary>

   MAE stays at $20.6k and the `size_sq` coefficient is `+0.00`. The hidden rule is a straight line in size, so a curve has nothing extra to explain. Adding features only helps when they carry real information.
   </details>
3. **Use real data.** Swap the made-up houses for the California housing dataset (downloads ~400 KB the first time).
   <details><summary>Solution</summary>

   Replace the first three lines after the imports with:
   ```python
   from sklearn.datasets import fetch_california_housing
   data = fetch_california_housing(as_frame=True)
   df = data.frame
   features = list(data.feature_names)          # 8 features
   X, y = df[features].to_numpy(), df["MedHouseVal"].to_numpy()   # price in $100k units
   ```
   Delete the last two lines (the example house uses the old 4 columns). The "truth" column will show `+0` for every feature because there is no known rule for real data. Expect R² around 0.6: real life is messier than a made-up rule.
   </details>

## Check yourself
1. Why do we measure MAE on the test houses instead of the training houses?
2. Why does the from-scratch version need feature scaling but `LinearRegression` doesn't?
3. The coefficient for `age_years` is −1.36. Say in plain words what that means.
4. RMSE is $25.8k and MAE is $20.6k. What would it mean if RMSE were $80k with the same MAE?

<details><summary>Answers</summary>

1. The model has already seen the training houses, so it can look better than it really is. The test houses act like new houses in the real world.
2. Gradient descent uses one learning rate for every weight. If columns have very different scales, the steps are wrong-sized for some of them. `LinearRegression` solves the equations directly, so scale doesn't matter.
3. Every extra year of age lowers the predicted price by about $1,360, if everything else stays the same.
4. A few predictions are very far off (RMSE squares the errors, so big misses dominate it), even though the typical miss is still ~$20k.
</details>

## Learn more (optional)
- Linear Regression, Clearly Explained (StatQuest): https://www.youtube.com/results?search_query=statquest+linear+regression+clearly+explained
- Gradient Descent, Step-by-Step (StatQuest): https://www.youtube.com/results?search_query=statquest+gradient+descent+step+by+step
- scikit-learn getting started: https://scikit-learn.org/stable/getting_started.html

## Next
→ [3.2 · Spam detector: logistic regression](../02-spam-detector-logistic-regression)
