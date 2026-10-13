# 3.6 · Churn predictor, end to end: data → pipeline → tuning → API

**What you build:** the way ML actually ships at companies. Messy customer data (with missing values) goes into a scikit-learn **Pipeline**. You compare two models with **cross-validated grid search**, check the winner on held-out data, **save** it to disk, and serve it from a **FastAPI** `/predict` endpoint with input validation and tests.
**Like you're 10:** a phone company wants to know which customers are about to leave, so they can call them *before* they go. Your model is the early-warning siren.

## Run it
```bash
cd level-3-classic-ml/06-churn-predictor-end-to-end-pipeline
pip install -r requirements.txt
python train.py                 # trains, compares models, saves churn_model.joblib
uvicorn api:app --reload        # serves it
```
Then in http://127.0.0.1:8000/docs → `POST /predict`:
```json
{"contract": "month-to-month", "tenure_months": 2, "monthly_charges": 110,
 "support_calls": 6, "internet": "fiber", "payment_method": "electronic-check"}
```
Test: `pytest -v`

## Key ideas
- **Pipeline = preprocessing + model in one object.** It fills missing values, scales numbers and one-hot encodes categories *the same way* in training and in production. Skipping this causes the most common real-world ML bug (training/serving skew).
- **GridSearchCV** tries hyperparameter combinations with 5-fold cross-validation, scoring by AUC.
- **Gradient boosting** (here `HistGradientBoostingClassifier`; in industry often XGBoost or LightGBM) is usually the king of tabular data, **but look who wins here**: logistic regression. The hidden churn rule in `data.py` is linear, so the simple model fits it best. Lesson: always compare against a simple baseline before reaching for something fancy.
- **Model artifact:** `joblib.dump` saves the whole pipeline; the API loads it once at startup.
- **Pydantic `Literal`** rejects bad inputs (`"contract": "forever"` → 422) before they reach the model.

## Your turn
1. Add a `/predict/batch` endpoint that accepts a list of customers.
2. Add feature importance using `sklearn.inspection.permutation_importance`, and expose it at `/explain`.
3. Containerize it with the Dockerfile pattern from project 1.7.

## Watch
- Gradient Boosting (StatQuest): https://www.youtube.com/results?search_query=statquest+gradient+boost+part+1
- scikit-learn pipelines: https://scikit-learn.org/stable/modules/compose.html
