# Part 2 · Machine learning

**Machine learning = learning rules from examples instead of writing the rules yourself.** Show the computer 500 houses with prices, and it works out how size and location affect price.

| # | Project | The computer learns to... |
|---|---------|---------------------------|
| 06 | [Predict house prices](06-predict-house-prices) | guess a number (price) |
| 07 | [Spam or not?](07-spam-or-not) | sort messages into two groups |
| 08 | [Flower guesser](08-flower-guesser) | pick a category, and show its reasoning |
| 09 | [Group customers](09-group-customers) | find groups nobody told it about |
| 10 | [Save a model and serve it as an API](10-save-a-model-and-serve-it) | answer predictions over the web (Part 1 + Part 2!) |

Install once:
```bash
pip install scikit-learn pandas joblib fastapi "uvicorn[standard]"
```
**The pattern you'll see in every project:** `model.fit(examples, answers)` learns, and `model.predict(new_thing)` uses what it learned.
