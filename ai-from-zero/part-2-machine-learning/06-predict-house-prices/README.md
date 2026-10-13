# 06 · Predict house prices

**What it does:** learns from 500 example houses, then guesses the price of any house you describe.

## Run it
```bash
cd part-2-machine-learning/06-predict-house-prices
python house_prices.py
python house_prices.py 200 4 2
```

## What you'll see
How far off it is on houses it never saw, the rules it discovered (very close to the hidden rule we used to make the data!), and a price for your house.

## The idea in one sentence
The model looks at many examples and finds the numbers ("+$2,500 per m²") that best explain the prices, then reuses them for new houses.

## Try this
1. Remove the `km` column everywhere. Does the average error get worse?
2. Change the hidden rule (e.g. `5_000 * size`) and check the model discovers your new rule.
