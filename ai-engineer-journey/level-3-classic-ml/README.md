# Level 3 · Classic machine learning: sorting toys into groups

Before deep learning, there's a toolbox of fast, explainable models that still power most business ML (credit scores, churn, fraud, pricing). An AI engineer who knows *when a simple model is enough* saves companies a fortune.

| # | Project | Model | Type |
|---|---------|-------|------|
| 3.1 | [House price predictor](01-house-price-predictor-linear-regression) | linear regression (from scratch + scikit-learn) | regression |
| 3.2 | [Spam detector](02-spam-detector-logistic-regression) | logistic regression + bag of words | classification |
| 3.3 | [Iris flower classifier](03-iris-flower-classifier-decision-tree) | decision tree you can read | classification |
| 3.4 | [Customer groups](04-customer-groups-kmeans-clustering) | k-means (from scratch + scikit-learn) | clustering (unsupervised) |
| 3.5 | [Model evaluation playground](05-model-evaluation-playground) | metrics, cross-validation, overfitting | the skill interviewers test most |
| 3.6 | [Churn predictor, end to end](06-churn-predictor-end-to-end-pipeline) | pipeline → tuning → saved model → API | how ML ships in real companies |

```bash
pip install numpy pandas scikit-learn matplotlib joblib fastapi uvicorn
```
**Watch alongside:** StatQuest's machine learning playlist explains every model here with pictures: https://www.youtube.com/@statquest/playlists
