# Guess an iris flower's type from 4 measurements, and PRINT the rules the model learned.
# Usage: python flower_guesser.py 5.9 3.0 5.1 1.8
import sys

from sklearn.datasets import load_iris
from sklearn.tree import DecisionTreeClassifier, export_text

flowers = load_iris()        # 150 real flowers measured by a botanist (comes with scikit-learn)
names = ["sepal length", "sepal width", "petal length", "petal width"]

model = DecisionTreeClassifier(max_depth=3)       # a "20 questions" style model
model.fit(flowers.data, flowers.target)

print("The questions the model learned to ask:\n")
print(export_text(model, feature_names=names))

measurements = [float(x) for x in sys.argv[1:5]] if len(sys.argv) >= 5 else [5.9, 3.0, 5.1, 1.8]
guess = model.predict([measurements])[0]
print(f"🌸 Measurements {measurements} → it's an iris {flowers.target_names[guess]}")
