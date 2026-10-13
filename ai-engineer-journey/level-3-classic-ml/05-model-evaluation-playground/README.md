# 3.5 · Model evaluation playground

**What you build:** five small experiments that show the evaluation ideas every ML interview asks about. You'll see them happen in the output, not just read about them.
**Like you're 10:** a model's score is a school report card. This project teaches you how report cards can **lie**: grading on homework the student already saw, a lazy student who always answers "no" and still gets 97%, and one lucky test day.

## Run it
```bash
cd level-3-classic-ml/05-model-evaluation-playground
pip install -r requirements.txt
python evaluation_playground.py
```

## The five lessons
1. **Under- vs. overfitting.** A degree-15 polynomial nails the training points and fails on new data.
2. **Accuracy lies on imbalanced data.** A "model" that never predicts fraud is ~97% accurate and useless.
3. **Confusion matrix.** It counts the four outcomes: true/false positives and negatives. On a real cancer dataset, a false negative is a missed cancer.
4. **Threshold = business decision.** Lower the threshold to catch more (recall ↑) at the cost of more false alarms (precision ↓).
5. **Cross-validation.** Average over 5 different splits so one lucky split can't fool you.

## Cheat sheet
| Metric | Question it answers | Use when |
|--------|---------------------|----------|
| Accuracy | % correct | classes are balanced |
| Precision | of my "yes" calls, how many were right? | false alarms are expensive (spam folder) |
| Recall | of the real "yes" cases, how many did I find? | misses are expensive (cancer, fraud) |
| F1 | balance of precision and recall | you need one number |
| AUC | how well does it *rank* positives above negatives? | comparing models regardless of threshold |
| MAE / RMSE | average error size | regression |

## Your turn
1. Add a `RandomForestClassifier` to the cross-validation comparison.
2. Find the threshold where recall ≥ 0.98 with the best precision possible.
3. Explain lesson 1 to a friend using the words *bias* and *variance*.

## Watch
- The Confusion Matrix (StatQuest): https://www.youtube.com/results?search_query=statquest+confusion+matrix
- ROC and AUC, Clearly Explained (StatQuest): https://www.youtube.com/results?search_query=statquest+roc+and+auc+clearly+explained
- Bias and Variance (StatQuest): https://www.youtube.com/results?search_query=statquest+machine+learning+fundamentals+bias+and+variance
