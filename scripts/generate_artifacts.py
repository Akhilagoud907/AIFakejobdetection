import os, json
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
import joblib

os.makedirs("m1_outputs", exist_ok=True)
os.makedirs("m2_outputs", exist_ok=True)

synth_real = [
    "We are hiring a software engineer with experience in Python, benefits included.",
    "Competitive salary, apply via our company portal, full-time position.",
    "Join our marketing team to collaborate on campaigns and analytics.",
    "Looking for a data analyst to build dashboards and support stakeholders.",
]
synth_fake = [
    "Congratulations! You have been selected. Send bank details to claim your job.",
    "Work from home, earn $5000 a week, no experience required, contact via WhatsApp.",
    "Urgent hiring, pay registration fee to start immediately.",
    "Send your login credentials to verify account and begin onboarding.",
]
texts = synth_real + synth_fake
y = np.array([0]*len(synth_real) + [1]*len(synth_fake))

vect = TfidfVectorizer(token_pattern=r"(?u)\b[a-zA-Z]{2,}\b", stop_words='english', max_features=1000)
X = vect.fit_transform(texts)

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)
clf = LogisticRegression(class_weight="balanced", max_iter=2000)
clf.fit(X_train, y_train)

joblib.dump(vect, "m1_outputs/tfidf_vectorizer.pkl")
joblib.dump(clf, "m2_outputs/logreg_best.joblib")
metrics = {"model": "LogisticRegression", "note": "synthetic demo artifacts"}
with open("m2_outputs/logreg_metrics.json", "w") as f:
    json.dump(metrics, f)

print("Artifacts created: m1_outputs/tfidf_vectorizer.pkl, m2_outputs/logreg_best.joblib, m2_outputs/logreg_metrics.json")
