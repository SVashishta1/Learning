# Predict a house price from its size, bedrooms and distance to the city centre.
# Usage: python house_prices.py 120 3 5      (120 m², 3 bedrooms, 5 km from centre)
import random
import sys

from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split

# 1. EXAMPLES: 500 made-up houses. (Real projects load a spreadsheet instead.)
random.seed(1)
houses, prices = [], []
for _ in range(500):
    size = random.randint(40, 250)
    bedrooms = random.randint(1, 5)
    km = random.randint(1, 30)
    price = 50_000 + 2_500 * size + 10_000 * bedrooms - 4_000 * km + random.randint(-20_000, 20_000)
    houses.append([size, bedrooms, km])
    prices.append(price)

# 2. Hide 20% of the houses. We'll test the model on houses it has never seen (like a real exam).
train_x, test_x, train_y, test_y = train_test_split(houses, prices, test_size=0.2, random_state=0)

# 3. LEARN
model = LinearRegression()
model.fit(train_x, train_y)

# 4. CHECK: how far off is it on the hidden houses, on average?
errors = [abs(guess - real) for guess, real in zip(model.predict(test_x), test_y)]
print(f"On houses it never saw, it's off by ${sum(errors) / len(errors):,.0f} on average.")

# 5. What rules did it discover? (The true hidden rule: +2,500 per m², +10,000 per bedroom, -4,000 per km)
size_rule, bedroom_rule, km_rule = model.coef_
print(f"It learned: +${size_rule:,.0f} per m², +${bedroom_rule:,.0f} per bedroom, -${abs(km_rule):,.0f} per km from the centre")

# 6. USE IT on a new house: the 3 numbers you typed, or an example house if you typed none
try:
    size, bedrooms, km = [float(x) for x in sys.argv[1:]] if len(sys.argv) > 1 else (120, 3, 5)
except ValueError:     # not numbers, or not exactly 3 of them
    sys.exit("Please give 3 numbers: size in m², bedrooms, km to the centre. Example: python house_prices.py 120 3 5")
price = model.predict([[size, bedrooms, km]])[0]
print(f"\n🏠 A {size:g} m², {bedrooms:g}-bedroom house {km:g} km from the centre: about ${price:,.0f}")
