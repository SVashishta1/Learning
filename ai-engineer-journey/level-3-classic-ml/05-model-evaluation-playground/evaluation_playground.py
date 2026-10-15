"""Project 3.5: the evaluation skills interviewers test most, as 5 small experiments."""
import numpy as np
from sklearn.datasets import load_breast_cancer
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.metrics import confusion_matrix, precision_score, recall_score, roc_auc_score
from sklearn.model_selection import cross_val_score, train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import PolynomialFeatures, StandardScaler
from sklearn.tree import DecisionTreeClassifier

rng = np.random.default_rng(0)
line = lambda title: print(f"\n{'=' * 8} {title} {'=' * (50 - len(title))}")

# ---- 1. Overfitting vs underfitting, shown with polynomials ----
line("1. Underfit / good fit / overfit")
# Only 20 training points: a degree-15 curve has enough wiggle room to pass through almost every one.
x = np.sort(rng.uniform(-3, 3, 20)); y = np.sin(x) + rng.normal(0, 0.25, 20)
x_new = np.sort(rng.uniform(-3, 3, 200)); y_new = np.sin(x_new) + rng.normal(0, 0.25, 200)
for degree in [1, 4, 15]:
    m = make_pipeline(PolynomialFeatures(degree), StandardScaler(), LinearRegression()).fit(x[:, None], y)
    tr = np.mean((m.predict(x[:, None]) - y) ** 2); te = np.mean((m.predict(x_new[:, None]) - y_new) ** 2)
    verdict = {1: "UNDERFIT (too simple)", 4: "GOOD FIT", 15: "OVERFIT (memorised noise)"}[degree]
    print(f"degree {degree:2d}: train error {tr:.3f} | NEW data error {te:8.3f}  <- {verdict}")

# ---- 2. Accuracy lies on imbalanced data ----
line("2. Why accuracy can lie")
y_fraud = (rng.random(1000) < 0.02).astype(int)           # 2% fraud
lazy = np.zeros(1000, dtype=int)                          # "model" that always says 'not fraud'
print(f"Lazy model accuracy: {np.mean(lazy == y_fraud):.1%}  ...but recall (fraud caught): {recall_score(y_fraud, lazy):.0%}")

# ---- 3. Confusion matrix, precision, recall on a real medical dataset ----
line("3. Confusion matrix (breast cancer dataset)")
X, y = load_breast_cancer(return_X_y=True)                # y: 1 = benign, 0 = malignant
y = 1 - y                                                 # flip so 1 = malignant (the thing we must catch)
X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.3, random_state=0, stratify=y)
clf = make_pipeline(StandardScaler(), LogisticRegression(max_iter=1000)).fit(X_tr, y_tr)
proba = clf.predict_proba(X_te)[:, 1]
tn, fp, fn, tp = confusion_matrix(y_te, proba > 0.5).ravel()
print(f"             predicted OK | predicted CANCER\ntruly OK     {tn:12d} | {fp:5d}  (false alarms)\ntruly CANCER {fn:12d} | {tp:5d}  <- {fn} missed cancers")
print(f"AUC (ranking quality, 1.0 = perfect): {roc_auc_score(y_te, proba):.3f}")

# ---- 4. Choosing a threshold = choosing a trade-off ----
line("4. Threshold trade-off")
print("threshold | precision | recall | missed cancers")
for t in [0.9, 0.7, 0.5, 0.3, 0.1]:
    pred = proba > t
    print(f"   {t:.1f}    |   {precision_score(y_te, pred):.2f}    |  {recall_score(y_te, pred):.2f}  | {np.sum((y_te == 1) & ~pred)}")
print("For cancer screening you'd pick a LOW threshold: a false alarm is better than a missed cancer.")

# ---- 5. Cross-validation: one split can be lucky; 5 splits tell the truth ----
line("5. Cross-validation")
for name, model in [("logistic regression", make_pipeline(StandardScaler(), LogisticRegression(max_iter=1000))),
                    ("deep decision tree", DecisionTreeClassifier(random_state=0))]:
    scores = cross_val_score(model, X, y, cv=5, scoring="recall")
    print(f"{name:20s} recall per fold {np.round(scores, 2)} -> mean {scores.mean():.3f} ± {scores.std():.3f}")
