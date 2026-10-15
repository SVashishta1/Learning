# 3.5 · Model evaluation playground

**What you'll build:** five small experiments that show the evaluation ideas every ML interview asks about. You'll see each one happen in the output, not just read about it.
**Like you're 10:** a model's score is a school report card. This project teaches you how report cards can **lie**: grading on homework the student already saw, a lazy student who always answers "no" and still gets 97%, and one lucky test day.
**Time:** ~1.5 h · **Builds on:** [3.4 Customer groups](../04-customer-groups-kmeans-clustering) (and the models from 3.1–3.3) · **Needs:** nothing extra

## Why this matters
Training a model takes one line; knowing whether it's any good is the real job. Teams ship broken models because they looked at the wrong number: 97% accuracy on fraud that catches no fraud, or a great score on data the model had already seen. Interviewers test this more than any algorithm, because it's what separates someone who can *run* ML from someone you can trust with it.

## What you'll learn
- **Overfitting vs underfitting**: a model can be too simple to learn the pattern, or so flexible it memorises the noise.
- **Why accuracy lies on imbalanced data**: when 98% of cases are "no", always saying "no" scores 98%.
- **Confusion matrix, precision, recall, AUC**: the four kinds of right and wrong, and the numbers built from them.
- **The threshold is a business decision**: the same model can be tuned to miss less or to cry wolf less.
- **Cross-validation**: averaging over several train/test splits so one lucky split can't fool you.

## Before you start
```bash
pip install -r requirements.txt
```
- `numpy`: random data and maths.
- `scikit-learn`: the models, metrics, cross-validation, and the built-in breast cancer dataset (no download).

No API key or internet needed.

## Run it
1. From the course root:
   ```bash
   cd level-3-classic-ml/05-model-evaluation-playground
   pip install -r requirements.txt
   ```
2. Run it:
   ```bash
   python evaluation_playground.py
   ```

### What you should see
```
======== 1. Underfit / good fit / overfit ==================
degree  1: train error 0.186 | NEW data error    0.279  <- UNDERFIT (too simple)
degree  4: train error 0.027 | NEW data error    0.078  <- GOOD FIT
degree 15: train error 0.004 | NEW data error  328.801  <- OVERFIT (memorised noise)

======== 2. Why accuracy can lie ===========================
Lazy model accuracy: 97.3%  ...but recall (fraud caught): 0%

======== 3. Confusion matrix (breast cancer dataset) =======
             predicted OK | predicted CANCER
truly OK              103 |     4  (false alarms)
truly CANCER            4 |    60  <- 4 missed cancers
AUC (ranking quality, 1.0 = perfect): 0.992

======== 4. Threshold trade-off ============================
threshold | precision | recall | missed cancers
   0.9    |   1.00    |  0.88  | 8
   0.7    |   1.00    |  0.92  | 5
   0.5    |   0.94    |  0.94  | 4
   0.3    |   0.86    |  0.95  | 3
   0.1    |   0.82    |  0.98  | 1
For cancer screening you'd pick a LOW threshold: a false alarm is better than a missed cancer.

======== 5. Cross-validation ===============================
logistic regression  recall per fold [0.98 0.95 0.93 0.95 1.  ] -> mean 0.962 ± 0.024
deep decision tree   recall per fold [0.93 0.88 0.88 0.93 0.93] -> mean 0.910 ± 0.023
```
What to look at:
- **Section 1**: the degree-15 curve has the *lowest* training error and by far the *worst* error on new data (328 vs 0.08).
- **Section 2**: 97% accuracy, 0% of fraud caught.
- **Section 4**: as the threshold goes down, recall goes up (fewer missed cancers) and precision goes down (more false alarms).
- **Section 5**: the per-fold scores vary (0.93 to 1.00). A single split could have shown you any one of those.

## How it works
The script is five independent experiments, each starting with a `line("...")` header.

1. **Under- vs overfitting.** It makes 20 noisy points on a sine wave (`np.sin(x)` plus noise), and 200 *new* points from the same curve. Then it fits three polynomial curves:
   - `PolynomialFeatures(degree)` adds columns x², x³, … up to x^degree, so plain `LinearRegression` can draw a curve instead of a line. `StandardScaler` keeps those powers on similar scales.
   - Degree 1 (a straight line) can't bend to follow a sine wave: high error everywhere. That's **underfitting** (also called high *bias*).
   - Degree 15 has 16 numbers to tune for only 20 points, so it wiggles through almost every training point, noise included, and swings wildly in between. Training error is tiny; new-data error explodes. That's **overfitting** (high *variance*).
   - Degree 4 is flexible enough for the real pattern but not for the noise: the good fit.
   ```
   underfit            good fit             overfit
   ────────            ╭─╮   ╭─            ╭╮╭╮ ╭╮╭─
                      ╯   ╰─╯               ╯╰╯╰╯╰╯
   ```
2. **Accuracy lies.** `y_fraud` marks about 2% of 1,000 transactions as fraud. The "lazy model" `np.zeros(1000)` predicts "not fraud" every time. Accuracy is ~97% because 97% of answers really are "not fraud", yet **recall** (share of real fraud caught) is 0%. On imbalanced data, always look at recall and precision for the rare class.
3. **Confusion matrix.** `load_breast_cancer()` is a real dataset of 569 tumour measurements (30 numbers each). Its labels use 1 = benign, so `y = 1 - y` flips them so 1 = malignant, the thing we must catch. A scaled logistic regression is trained, and `predict_proba(...)[:, 1]` gives each test patient's probability of cancer. `confusion_matrix(...).ravel()` returns the four counts:
   ```
                     predicted OK          predicted CANCER
   truly OK          TN (true negative)    FP (false positive = false alarm)
   truly CANCER      FN (false negative)   TP (true positive)
                     = missed cancer!
   ```
   **AUC** (area under the ROC curve) asks: if you pick one cancer patient and one healthy patient at random, how often does the model give the cancer patient the higher score? 1.0 = always, 0.5 = coin flip. It ignores the threshold, which makes it good for comparing models.
4. **Threshold trade-off.** The model outputs a probability; *you* choose the cut-off. The loop tries 0.9 down to 0.1 and prints **precision** (of the patients flagged, how many really had cancer?) and **recall** (of the real cancers, how many were flagged?). A false alarm means an extra test; a miss can cost a life, so screening uses a low threshold. A spam filter would choose the opposite.
5. **Cross-validation.** `cross_val_score(model, X, y, cv=5, scoring="recall")` splits the data into 5 parts, trains on 4 and tests on the 5th, five times, so every patient is tested once. The mean is a more trustworthy score, and the ± (standard deviation) tells you how much it depends on luck. Logistic regression beats an unlimited-depth decision tree here (0.962 vs 0.910): the deep tree overfits, just like the degree-15 curve.

### Cheat sheet
| Metric | Question it answers | Use when |
|--------|---------------------|----------|
| Accuracy | % correct | classes are balanced |
| Precision | of my "yes" calls, how many were right? | false alarms are expensive (spam folder) |
| Recall | of the real "yes" cases, how many did I find? | misses are expensive (cancer, fraud) |
| F1 | balance of precision and recall | you need one number |
| AUC | how well does it *rank* positives above negatives? | comparing models regardless of threshold |
| MAE / RMSE | average error size | regression |

## If something goes wrong
- **`UndefinedMetricWarning: Precision is ill-defined`** (after you edit thresholds) → at that threshold the model flagged nobody, so precision is 0/0. scikit-learn reports 0 and warns. Use a lower threshold.
- **`ConvergenceWarning: lbfgs failed to converge`** (if you remove `StandardScaler`) → logistic regression needs scaled inputs or more iterations. Keep the scaler, or raise `max_iter`.
- **Your numbers differ a little from the sample** → different numpy or scikit-learn versions can produce slightly different random numbers or solver results. The patterns (overfit error explodes, lazy model 0% recall) stay the same.
- **`ModuleNotFoundError: No module named 'sklearn'`** → activate your virtual environment and run `pip install -r requirements.txt`.

## Try this
1. **Add a random forest** to the cross-validation comparison in section 5. Does a forest of trees overfit less than one deep tree?
   <details><summary>Solution</summary>

   Add `from sklearn.ensemble import RandomForestClassifier` to the imports, and add this entry to the list in section 5:
   ```python
   ("random forest", RandomForestClassifier(n_estimators=100, random_state=0)),
   ```
   You get mean recall 0.944 ± 0.043: better than the single deep tree (0.910) because 100 trees voting average out each other's mistakes, but still below logistic regression on this dataset.
   </details>
2. **Find the safest threshold.** Find the threshold where recall ≥ 0.98 with the best possible precision.
   <details><summary>Solution</summary>

   Add at the end:
   ```python
   for t in np.arange(0.5, 0.0, -0.01):          # try 0.50, 0.49, ... downwards
       pred = proba > t
       if recall_score(y_te, pred) >= 0.98:
           print(f"threshold {t:.2f}: precision {precision_score(y_te, pred):.2f}, recall {recall_score(y_te, pred):.2f}")
           break
   ```
   Going down from 0.5, the first threshold that reaches the recall target keeps the most precision. You get about 0.10 with precision 0.82. (`sklearn.metrics.precision_recall_curve` does this search for you.)
   </details>
3. **Explain section 1** to a friend using the words *bias* and *variance*.
   <details><summary>Hint</summary>

   Bias = being wrong in a consistent way because the model is too simple (a straight line can never be a wave). Variance = being too sensitive to the exact training points, so a different sample would give a very different curve (degree 15). Good models balance both. Check yourself: change the random seed in `np.random.default_rng(0)` and re-run; the degree-15 new-data error jumps around a lot, the degree-1 error barely moves.
   </details>

## Check yourself
1. Why is "97% accuracy" not good news for a fraud model?
2. A model has training error 0.004 and new-data error 328. What's the name for this, and what's one way to fix it?
3. In cancer screening, which is worse: a false positive or a false negative? Which way should you move the threshold?
4. Why is a 5-fold cross-validation score more trustworthy than one train/test split?

<details><summary>Answers</summary>

1. If only ~3% of transactions are fraud, a model that never says "fraud" also gets ~97%. Accuracy hides that it catches nothing; check recall on the fraud class.
2. Overfitting. Use a simpler model (lower degree), get more training data, or add regularisation.
3. A false negative (a missed cancer). Lower the threshold so more patients are flagged: recall goes up, at the cost of more false alarms.
4. It averages five different test sets, so one unusually easy or hard split can't mislead you, and the spread shows how stable the score is.
</details>

## Learn more (optional)
- The Confusion Matrix (StatQuest): https://www.youtube.com/results?search_query=statquest+confusion+matrix
- ROC and AUC, Clearly Explained (StatQuest): https://www.youtube.com/results?search_query=statquest+roc+and+auc+clearly+explained
- Bias and Variance (StatQuest): https://www.youtube.com/results?search_query=statquest+machine+learning+fundamentals+bias+and+variance
- Cross Validation (StatQuest): https://www.youtube.com/results?search_query=statquest+cross+validation

## Next
→ [3.6 · Churn predictor, end to end](../06-churn-predictor-end-to-end-pipeline)
