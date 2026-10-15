# Part 2 · Machine learning

**Machine learning = learning rules from examples instead of writing the rules yourself.** Show the computer 500 houses with prices, and it works out how size and location affect price.

**Time:** about 1 week at 1 hour a day · **Before this part:** [00 · Start here](../00-start-here) set up, and ideally [Part 1](../part-1-apis) (lesson 10 builds an API like Part 1's)

| # | Project | The computer learns to... |
|---|---------|---------------------------|
| 06 | [Predict house prices](06-predict-house-prices) | guess a number (price) from examples |
| 07 | [Spam or not?](07-spam-or-not) | sort messages into two groups, and say how sure it is |
| 08 | [Flower guesser](08-flower-guesser) | pick one of 3 categories, and show its reasoning |
| 09 | [Group customers](09-group-customers) | find groups nobody told it about |
| 10 | [Save a model and serve it as an API](10-save-a-model-and-serve-it) | answer predictions over the web (Part 1 + Part 2!) |

## Install once for this part
Open a terminal in the course folder (`ai-from-zero`), switch your venv on ([00 · Start here](../00-start-here), step 6), then:
```bash
pip install scikit-learn joblib fastapi "uvicorn[standard]"
```
- `scikit-learn`: the standard Python library for classic machine learning (it also installs `numpy` and `scipy` for the maths). You install it as `scikit-learn` but import it as `sklearn`.
- `joblib`: saves a trained model to a file and loads it back (lesson 10).
- `fastapi` and `uvicorn[standard]`: serve the model as an API (lesson 10). Already installed if you did Part 1.

No API keys and no internet needed once installed: all data is made up by the code or built into scikit-learn.

**The pattern you'll see in every project:** `model.fit(examples, answers)` learns, and `model.predict(new_thing)` uses what it learned.

## After this part you'll be able to
- Explain the difference between regression (predict a number), classification (pick a category) and clustering (find groups), and when to use each.
- Train, test and use scikit-learn models: linear regression, logistic regression, decision trees and k-means.
- Judge a model fairly with a hidden test set, and spot when a model is memorising instead of learning.
- Turn text into numbers a model can learn from, and scale features so none of them drowns out the others.
- Save a trained model to a file and serve its predictions through a FastAPI web API.

## Next
Start with → [06 · Predict house prices](06-predict-house-prices). When you finish lesson 10, go on to → [Part 3 · Neural networks](../part-3-neural-networks).
