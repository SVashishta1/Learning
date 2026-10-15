# 06 · Predict house prices

**What you'll build:** a program that learns from 500 example houses, then guesses the price of any house you describe.
**Time:** ~30 min · **Builds on:** [05 · Put your API on the internet](../../part-1-apis/05-put-your-api-on-the-internet) (only Python basics are needed) · **Needs:** nothing extra

Like you're 10: you look at lots of houses and their price tags until you can guess "big house near town = expensive" without being told the rule. The computer does the same, with maths.

## Why this matters
Predicting a number from examples is called **regression**, and it's everywhere: house-price estimates on property sites, delivery-time estimates, sales forecasts, energy demand. Linear regression is usually the first model a data scientist tries, because it's fast and you can read what it learned. The pattern you learn here (`fit` to learn, `predict` to use) is the same for every scikit-learn model in this part.

## What you'll learn
- **Machine learning**: the computer finds the rules from examples, instead of you writing the rules.
- **Features and label**: the inputs you know (size, bedrooms, distance) and the answer you want to predict (price).
- **Training and test sets**: learn from 80% of the examples and keep 20% hidden as a fair exam.
- **Linear regression**: a model that learns one "price per unit" number (a **coefficient**) for each feature and adds them up.
- **Error**: how far the guesses are from the real prices, on houses the model never saw.

## Before you start
- Venv on, then this part's install line (once for all of Part 2):
  ```bash
  pip install scikit-learn joblib fastapi "uvicorn[standard]"
  ```
  This lesson only uses `scikit-learn` (the most popular Python library for classic machine learning). The others are for lesson 10.
- No API key needed. No internet needed after installing.

## Run it
1. From the course folder (`ai-from-zero`):
   ```bash
   cd part-2-machine-learning/06-predict-house-prices
   python house_prices.py
   ```
2. Now describe your own house: size in m², bedrooms, km from the centre:
   ```bash
   python house_prices.py 200 4 2
   ```

### What you should see
```
On houses it never saw, it's off by $10,752 on average.
It learned: +$2,511 per m², +$10,204 per bedroom, -$4,069 per km from the centre

🏠 A 120 m², 3-bedroom house 5 km from the centre: about $359,814
```
and for `200 4 2`, the last line becomes:
```
🏠 A 200 m², 4-bedroom house 2 km from the centre: about $583,106
```
Look at the second line. The hidden rule used to make the data was **+2,500 per m², +10,000 per bedroom, -4,000 per km**. The model was never told this rule, yet it found almost exactly those numbers just from the examples. That's machine learning.

## How it works
```
500 example houses ──split──▶ 400 to learn from ──model.fit()──▶ learned rules
                          └──▶ 100 hidden ──model.predict()──▶ compare with real prices ──▶ average error
your house ──model.predict()──▶ price
```
1. **Make examples.** The loop runs 500 times. Each time it picks a random `size`, `bedrooms` and `km`, then computes `price` with a hidden rule plus some random "noise" (`random.randint(-20_000, 20_000)`), because real prices never follow a rule exactly. `houses` gets the features `[size, bedrooms, km]`; `prices` gets the answer. `random.seed(1)` makes the "random" numbers the same on every run, so your output matches this README. (Real projects load real data from a spreadsheet instead.)
2. **Hide 20%.** `train_test_split(houses, prices, test_size=0.2, random_state=0)` shuffles the examples and splits them: 400 for training (`train_x`, `train_y`), 100 for testing (`test_x`, `test_y`). Testing on houses the model already saw would be like marking an exam the student had the answers to.
3. **Learn.** `model = LinearRegression()` makes an empty model. `model.fit(train_x, train_y)` finds the numbers that make `start + a × size + b × bedrooms + c × km` as close as possible to the real prices.
4. **Check.** `model.predict(test_x)` guesses the 100 hidden prices. `errors` is how far off each guess is (`abs` drops the minus sign), and the average is printed. About $10,000 is good here, because the noise alone adds up to ±$20,000.
5. **Read the rules.** `model.coef_` holds the learned coefficients `a`, `b`, `c` (one per feature, in the same order as the features), so they're unpacked into `size_rule, bedroom_rule, km_rule`.
6. **Use it.** `sys.argv[1:]` is the list of numbers you typed after the file name. If you typed none, it uses an example house (120, 3, 5). If they aren't exactly 3 numbers, the `try`/`except ValueError` prints a helpful message instead of crashing. `model.predict([[size, bedrooms, km]])[0]` gives the price. It needs a list of houses (hence the double brackets), and `[0]` takes the first (only) answer.

## If something goes wrong
- **`ModuleNotFoundError: No module named 'sklearn'`** → the package is called `scikit-learn` when installing but `sklearn` when importing. Switch your venv on and run the pip line above.
- **`Please give 3 numbers: size in m², bedrooms, km to the centre`** → you typed too few or too many values, or a word. Example: `python house_prices.py 120 3 5`.
- **`can't open file ... house_prices.py`** → you're not in the lesson folder. `cd part-2-machine-learning/06-predict-house-prices` from the course folder.
- **Your numbers differ from this README** → only if you changed the code or the `random.seed`. Different random examples give slightly different learned rules; that's expected.
- **A silly price for a silly house (e.g. a negative price for a 5 m² house 200 km away)** → the model only saw sizes 40–250 m² and distances 1–30 km. Outside that range it's guessing with a straight line, and straight lines go below zero.

## Try this
1. Remove the `km` feature completely, so the model only knows size and bedrooms. Does the average error get worse?
2. Change the hidden rule to `5_000 * size`. Does the model discover your new rule?
3. Add a fourth feature: `garden` (0 or 1) that adds $30,000 to the price. Can the model find the garden bonus?

<details><summary>Hints and solutions</summary>

1. Change 4 lines: `houses.append([size, bedrooms])`; `size_rule, bedroom_rule = model.coef_`; the `print` after it (remove the km part); and `price = model.predict([[size, bedrooms]])[0]`. The error grows from about **$10,752 to $28,927**, because distance really does affect price and the model can no longer see it.
2. In the `price = ...` line, change `2_500 * size` to `5_000 * size`. The output says `It learned: +$5,011 per m², ...`. It found your rule.
3. In the loop add `garden = random.randint(0, 1)`, add `+ 30_000 * garden` to the price, and use `houses.append([size, bedrooms, km, garden])`. Then unpack `size_rule, bedroom_rule, km_rule, garden_rule = model.coef_` and print `garden_rule`. In step 6, use `size, bedrooms, km, garden = ... else (120, 3, 5, 1)` and `model.predict([[size, bedrooms, km, garden]])`. It learns about **+$30,764 for a garden**, and the average error drops slightly to about $9,948.
</details>

## Check yourself
1. Why do we test on houses the model never saw instead of the ones it learned from?
2. What does `model.fit(train_x, train_y)` do, in plain words? And `model.predict(...)`?
3. The model learned +$2,511 per m², not exactly +$2,500. Why not exactly?
4. Why does removing the `km` feature make the predictions worse?

<details><summary>Answers</summary>

1. To get an honest score. A model can memorise examples it has seen; the real question is how well it does on new houses.
2. `fit` looks at the examples and their answers and works out the best rule (the coefficients). `predict` applies that rule to new inputs to produce answers.
3. The prices include random noise (±$20,000), and the model only saw 400 examples, so its best estimate is close to the true rule but not perfect.
4. Price really depends on distance. Without that information, the model can't tell a house in the centre from an identical one 30 km away, so its guesses are off by more.
</details>

## Learn more (optional)
- scikit-learn's guide to linear models: https://scikit-learn.org/stable/modules/linear_model.html
- Google's free Machine Learning Crash Course, "Linear regression": https://developers.google.com/machine-learning/crash-course
- Video: search YouTube for "StatQuest linear regression" (clear, friendly explanations).

## Next
→ [07 · Spam or not?](../07-spam-or-not)
