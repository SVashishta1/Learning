"""Project 3.6 step 1: build a full scikit-learn Pipeline, tune it, evaluate it honestly, save it."""
import joblib
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, roc_auc_score
from sklearn.model_selection import GridSearchCV, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from data import make_customers

NUMERIC = ["tenure_months", "monthly_charges", "support_calls"]
CATEGORICAL = ["contract", "internet", "payment_method"]

df = make_customers()
print(f"{len(df)} customers, churn rate {df.churned.mean():.1%}")
X, y = df[NUMERIC + CATEGORICAL], df.churned
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=0, stratify=y)

# Preprocessing lives INSIDE the pipeline, so training and serving can never disagree
prep = ColumnTransformer([
    ("num", Pipeline([("fill", SimpleImputer(strategy="median")), ("scale", StandardScaler())]), NUMERIC),
    ("cat", OneHotEncoder(handle_unknown="ignore"), CATEGORICAL),
])

candidates = {
    "logistic_regression": (LogisticRegression(max_iter=1000), {"model__C": [0.1, 1, 10]}),
    "gradient_boosting": (HistGradientBoostingClassifier(random_state=0), {"model__max_depth": [3, 6], "model__learning_rate": [0.05, 0.1]}),
}
best_name, best_search = None, None
for name, (model, grid) in candidates.items():
    search = GridSearchCV(Pipeline([("prep", prep), ("model", model)]), grid, cv=5, scoring="roc_auc", n_jobs=-1)
    search.fit(X_train, y_train)
    print(f"{name:20s} best CV AUC {search.best_score_:.3f} with {search.best_params_}")
    if best_search is None or search.best_score_ > best_search.best_score_:
        best_name, best_search = name, search

model = best_search.best_estimator_
proba = model.predict_proba(X_test)[:, 1]
print(f"\nWinner: {best_name}. Held-out test AUC {roc_auc_score(y_test, proba):.3f}")
print(classification_report(y_test, proba > 0.5, digits=3))

joblib.dump({"pipeline": model, "features": NUMERIC + CATEGORICAL, "model_name": best_name}, "churn_model.joblib")
print("Saved churn_model.joblib  ->  now run: uvicorn api:app --reload")
