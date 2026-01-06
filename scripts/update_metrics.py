import json, joblib
from sklearn.metrics import accuracy_score, precision_recall_fscore_support, roc_auc_score, confusion_matrix

X_train, X_test, y_train, y_test = joblib.load("m1_outputs/train_test_split.joblib")
clf = joblib.load("m2_outputs/logreg_best.joblib")

y_prob = clf.predict_proba(X_test)[:, 1]
y_pred = (y_prob >= 0.5).astype(int)

acc = accuracy_score(y_test, y_pred)
prec, rec, f1, _ = precision_recall_fscore_support(y_test, y_pred, average="binary")
auc = roc_auc_score(y_test, y_prob)
cm = confusion_matrix(y_test, y_pred)

metrics = {
    "model": "LogisticRegression",
    "accuracy": acc,
    "precision": prec,
    "recall": rec,
    "f1": f1,
    "auc": auc,
    "confusion_matrix": cm.tolist()
}

with open("m2_outputs/logreg_metrics.json", "w") as f:
    json.dump(metrics, f, indent=4)

print("Updated metrics written to m2_outputs/logreg_metrics.json")
