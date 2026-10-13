# 3.1 · House price predictor: linear regression

**What you build:** a model that predicts a house's price from its size, bedrooms, age and distance to the city. First **from scratch** with the gradient descent you wrote in Level 2, then in 2 lines with scikit-learn.
**Like you're 10:** a real-estate agent learns rules like "+$2,500 per square metre, –$4,000 per km from the centre". Linear regression finds those numbers for you.

## Run it
```bash
cd level-3-classic-ml/01-house-price-predictor-linear-regression
pip install -r requirements.txt
python house_prices.py
```
The data is made up (`make_data.py`) with a **hidden rule**, so you can see the model rediscover it: the learned coefficients come out close to the truth.

## Key ideas
- **Train/test split:** never grade a model on data it trained on. That's like grading a student on questions they've seen the answers to.
- **Feature scaling:** put every column on a similar scale before gradient descent.
- **Metrics:** MAE = average miss in $ (easy to explain). RMSE punishes big misses more. **R²** = share of price variation explained (1.0 is perfect).
- **Interpretability:** each coefficient is a human-readable rule. Banks and governments love this.

## Your turn
1. Remove `km_to_center` from `features`. How much worse does MAE get?
2. Add a feature `size_m2 ** 2` (a curve!). Does it help? Why not, given the hidden rule?
3. Use real data: `from sklearn.datasets import fetch_california_housing` (downloads ~400 KB).

## Watch
- Linear Regression, Clearly Explained (StatQuest): https://www.youtube.com/results?search_query=statquest+linear+regression+clearly+explained
- scikit-learn getting started: https://scikit-learn.org/stable/getting_started.html
