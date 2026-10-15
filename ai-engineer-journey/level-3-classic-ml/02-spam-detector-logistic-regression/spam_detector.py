"""Project 3.2: a spam detector = bag-of-words + logistic regression.

Usage:  python spam_detector.py                -> train + evaluate on messages.csv (70 messages)
        python spam_detector.py --full         -> also try the real 5,574-message UCI SMS dataset
        python spam_detector.py "your text"    -> classify your own message
"""
import io
import sys
import urllib.request
import zipfile
from pathlib import Path

import pandas as pd
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline

UCI_URL = "https://archive.ics.uci.edu/static/public/228/sms+spam+collection.zip"
SMALL_DATA = Path(__file__).with_name("messages.csv")   # works whichever folder you run from
THRESHOLD = 0.5   # call it spam when the model is more than 50% sure


def load(full: bool) -> pd.DataFrame:
    if full:
        try:
            raw = urllib.request.urlopen(UCI_URL, timeout=20).read()
            text = zipfile.ZipFile(io.BytesIO(raw)).read("SMSSpamCollection").decode("utf-8", "ignore")
            rows = [line.split("\t", 1) for line in text.splitlines() if "\t" in line]
            print(f"Loaded {len(rows)} real SMS messages from UCI")
            return pd.DataFrame(rows, columns=["label", "text"])
        except Exception as e:
            print(f"(couldn't download the full dataset: {e}; using messages.csv)")
    return pd.read_csv(SMALL_DATA)


def main():
    args = [a for a in sys.argv[1:] if a != "--full"]
    df = load("--full" in sys.argv)
    X_train, X_test, y_train, y_test = train_test_split(df.text, df.label, test_size=0.3, random_state=1, stratify=df.label)

    # CountVectorizer = "bag of words": each message becomes word counts. Order is ignored, like a bag.
    # LogisticRegression learns a weight per word: positive weights push toward "spam".
    model = make_pipeline(CountVectorizer(lowercase=True, ngram_range=(1, 2), min_df=1), LogisticRegression(max_iter=1000, C=5))
    model.fit(X_train, y_train)

    # predict_proba gives [P(ham), P(spam)] per message; classes_ is alphabetical, so column 1 is "spam"
    p_spam_test = model.predict_proba(X_test)[:, 1]
    pred = ["spam" if p > THRESHOLD else "ham" for p in p_spam_test]
    print(classification_report(y_test, pred, digits=3))
    print("Confusion matrix (rows = truth, cols = prediction) [ham, spam]:")
    print(confusion_matrix(y_test, pred, labels=["ham", "spam"]))

    vec, clf = model[0], model[-1]               # the two steps of the pipeline: vectoriser, then classifier
    words = vec.get_feature_names_out()
    order = clf.coef_[0].argsort()
    print("\nMost SPAMMY words:", ", ".join(words[order[-12:]][::-1]))
    print("Most HAMMY words: ", ", ".join(words[order[:12]]))

    for msg in args or ["Claim your free prize now", "Can we meet for coffee tomorrow?"]:
        p_spam = model.predict_proba([msg])[0, 1]
        print(f"\n'{msg}' -> {'SPAM' if p_spam > THRESHOLD else 'ham'} ({p_spam:.0%} spam)")


if __name__ == "__main__":
    main()
