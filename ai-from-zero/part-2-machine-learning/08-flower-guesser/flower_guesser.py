# Guess an iris flower's type from 4 measurements, and PRINT the rules the model learned.
# Usage: python flower_guesser.py 5.9 3.0 5.1 1.8
import sys

from sklearn.datasets import load_iris
from sklearn.tree import DecisionTreeClassifier, export_text

flowers = load_iris()        # 150 real flowers measured by a botanist (comes with scikit-learn)
names = ["sepal length", "sepal width", "petal length", "petal width"]

# A "20 questions" style model. max_depth=3: at most 3 questions in a row. random_state=0: same tree every run.
model = DecisionTreeClassifier(max_depth=3, random_state=0)
model.fit(flowers.data, flowers.target)      # data = the 4 measurements, target = the type (0, 1 or 2)

print("The questions the model learned to ask (all sizes in cm):\n")
print(export_text(model, feature_names=names, class_names=list(flowers.target_names)))
# score() = the share of the 150 flowers it labels correctly (flowers it studied, so it's an easy test)
print(f"It gets {model.score(flowers.data, flowers.target):.0%} of the 150 flowers right.\n")

# Your 4 measurements in cm, or an example flower if you typed none
try:
    measurements = [float(x) for x in sys.argv[1:]] if len(sys.argv) > 1 else [5.9, 3.0, 5.1, 1.8]
except ValueError:
    sys.exit("Please give numbers only. Example: python flower_guesser.py 5.0 3.4 1.5 0.2")
if len(measurements) != 4:
    sys.exit("Please give exactly 4 numbers: sepal length, sepal width, petal length, petal width (in cm).")
guess = model.predict([measurements])[0]     # a number: 0, 1 or 2
print(f"🌸 Measurements {measurements} → it's an iris {flowers.target_names[guess]}")
