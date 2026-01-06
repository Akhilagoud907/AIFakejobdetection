import os, re, json
import numpy as np
import pandas as pd
import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, precision_recall_fscore_support, roc_auc_score, confusion_matrix
from sklearn.model_selection import GridSearchCV

DATA_PATH = "fake_job_postings.csv"

def basic_clean(text: str) -> str:
    text = str(text).lower()
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"http\S+|www\.\S+", " ", text)
    text = re.sub(r"[^a-z\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text

os.makedirs("m1_outputs", exist_ok=True)
os.makedirs("m2_outputs", exist_ok=True)

print(f"Loading {DATA_PATH}...")
df = pd.read_csv(DATA_PATH, low_memory=False)
text_cols = [c for c in ['title','company_profile','description','requirements','benefits'] if c in df.columns]
df = df.fillna("")
df['combined_text_raw'] = df[text_cols].agg(' '.join, axis=1).astype(str)
df['cleaned_text'] = df['combined_text_raw'].apply(basic_clean)

label_col = 'fraudulent' if 'fraudulent' in df.columns else None
if not label_col:
    raise RuntimeError("fraudulent label column not found in CSV")

print("Fitting TF-IDF...")
tfidf = TfidfVectorizer(max_features=3000, ngram_range=(1,2), min_df=2, max_df=0.95, sublinear_tf=True, token_pattern=r"(?u)\b[a-zA-Z]{2,}\b")
X = tfidf.fit_transform(df['cleaned_text'].tolist())
joblib.dump(tfidf, "m1_outputs/tfidf_vectorizer.pkl")
print("Saved vectorizer to m1_outputs/tfidf_vectorizer.pkl")

le = LabelEncoder()
y = le.fit_transform(df[label_col].values)
strat = y if len(np.unique(y))>1 else None
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=strat)
joblib.dump((X_train, X_test, y_train, y_test), "m1_outputs/train_test_split.joblib")
print("Saved split to m1_outputs/train_test_split.joblib")

params = {"C": [0.01,0.1,1,10], "solver": ["liblinear","lbfgs"], "penalty": ["l2"]}
logreg = LogisticRegression(class_weight="balanced", max_iter=5000)
print("Grid searching Logistic Regression...")
grid = GridSearchCV(estimator=logreg, param_grid=params, scoring="f1", cv=5, verbose=1, n_jobs=-1)
grid.fit(X_train, y_train)
best_lr = grid.best_estimator_
print("Best params:", grid.best_params_)

y_prob = best_lr.predict_proba(X_test)[:,1]
y_pred = (y_prob>=0.5).astype(int)
acc = accuracy_score(y_test, y_pred)
prec, rec, f1, _ = precision_recall_fscore_support(y_test, y_pred, average="binary")
auc = roc_auc_score(y_test, y_prob)
cm = confusion_matrix(y_test, y_pred)

joblib.dump(best_lr, "m2_outputs/logreg_best.joblib")
metrics = {
    "model": "LogisticRegression",
    "best_params": grid.best_params_,
    "accuracy": acc,
    "precision": prec,
    "recall": rec,
    "f1": f1,
    "auc": auc,
    "confusion_matrix": cm.tolist()
}
with open("m2_outputs/logreg_metrics.json", "w") as f:
    json.dump(metrics, f, indent=4)
print("Saved best model and metrics to m2_outputs/")
