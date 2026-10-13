"""Project 3.3: classify iris flowers with a decision tree you can READ like a flowchart."""
from sklearn.datasets import load_iris
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier, export_text

iris = load_iris()                         # 150 flowers, 4 measurements each, 3 species (built into sklearn)
X_train, X_test, y_train, y_test = train_test_split(iris.data, iris.target, test_size=0.3, random_state=42, stratify=iris.target)

tree = DecisionTreeClassifier(max_depth=3, random_state=0).fit(X_train, y_train)
print(f"Test accuracy: {accuracy_score(y_test, tree.predict(X_test)):.1%}\n")

print("The rules the tree learned (read top to bottom):")
print(export_text(tree, feature_names=list(iris.feature_names)))

print("Which measurements mattered most:")
for name, imp in sorted(zip(iris.feature_names, tree.feature_importances_), key=lambda t: -t[1]):
    print(f"  {name:20s} {'█' * int(imp * 40)} {imp:.2f}")

# Depth experiment: deeper trees memorise the training set (overfitting)
print("\ndepth | train acc | test acc")
for depth in [1, 2, 3, 5, 10, None]:
    t = DecisionTreeClassifier(max_depth=depth, random_state=0).fit(X_train, y_train)
    print(f"{str(depth):5s} | {t.score(X_train, y_train):9.1%} | {t.score(X_test, y_test):8.1%}")

flower = [[5.9, 3.0, 5.1, 1.8]]   # sepal length, sepal width, petal length, petal width (cm)
print(f"\nMy flower {flower[0]} is a: {iris.target_names[tree.predict(flower)[0]]}")

try:
    import matplotlib.pyplot as plt
    from sklearn.tree import plot_tree
    plt.figure(figsize=(12, 6))
    plot_tree(tree, feature_names=iris.feature_names, class_names=iris.target_names, filled=True)
    plt.savefig("iris_tree.png", dpi=110, bbox_inches="tight")
    print("Saved iris_tree.png")
except ImportError:
    pass
