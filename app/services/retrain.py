import os
import json
import shutil
from datetime import datetime
from typing import Optional, Tuple, Dict, List

import numpy as np
import pandas as pd
import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_recall_fscore_support, roc_auc_score

from app.storage.db import fetch_flagged_posts
from app.models.inference import basic_clean

DATA_PATH_DEFAULT = "fake_job_postings.csv"
TFIDF_PATH = os.path.join("m1_outputs", "tfidf_vectorizer.pkl")
MODEL_OUT_PATH = os.path.join("m2_outputs", "logreg_best.joblib")
MODEL_METRICS_PATH = os.path.join("m2_outputs", "logreg_metrics.json")
VERSIONS_DIR = os.path.join("m2_versions")

os.makedirs(VERSIONS_DIR, exist_ok=True)


def _load_dataset(data_path: str) -> Tuple[List[str], np.ndarray]:
    texts: List[str] = []
    labels: List[int] = []
    if os.path.exists(data_path):
        df = pd.read_csv(data_path, low_memory=False)
        text_cols = [c for c in ['title','company_profile','description','requirements','benefits'] if c in df.columns]
        df = df.fillna("")
        if text_cols:
            df['combined_text_raw'] = df[text_cols].agg(' '.join, axis=1).astype(str)
            base_texts = df['combined_text_raw'].tolist()
        elif 'description' in df.columns:
            base_texts = df['description'].astype(str).tolist()
        else:
            base_texts = []
        if 'fraudulent' in df.columns:
            base_labels = df['fraudulent'].astype(int).tolist()
        else:
            base_labels = []
        if base_texts and base_labels and len(base_texts) == len(base_labels):
            texts.extend(base_texts)
            labels.extend(base_labels)
    return texts, np.array(labels) if labels else np.array([])


def _append_validated(texts: List[str], labels: List[int]) -> Tuple[List[str], List[int]]:
    flagged = fetch_flagged_posts()
    for item in flagged:
        if getattr(item, "validated_label", None) is None:
            continue
        texts.append(item.description)
        labels.append(int(item.validated_label))
    return texts, labels


def _train(texts: List[str], labels: List[int]) -> Tuple[TfidfVectorizer, LogisticRegression, Dict]:
    cleaned = [basic_clean(t) for t in texts]
    vectorizer = TfidfVectorizer(max_features=4000, ngram_range=(1,2), min_df=2, max_df=0.95, sublinear_tf=True, token_pattern=r"(?u)\b[a-zA-Z]{2,}\b")
    X = vectorizer.fit_transform(cleaned)
    strat = labels if len(set(labels)) > 1 else None
    X_train, X_test, y_train, y_test = train_test_split(X, labels, test_size=0.2, random_state=42, stratify=strat)
    clf = LogisticRegression(class_weight="balanced", max_iter=5000, solver="lbfgs")
    clf.fit(X_train, y_train)

    y_prob = clf.predict_proba(X_test)[:, 1]
    y_pred = (y_prob >= 0.5).astype(int)
    acc = accuracy_score(y_test, y_pred)
    prec, rec, f1, _ = precision_recall_fscore_support(y_test, y_pred, average="binary")
    auc = roc_auc_score(y_test, y_prob) if len(set(y_test)) > 1 else float(acc)
    metrics = {
        "model": "LogisticRegression",
        "accuracy": float(acc),
        "precision": float(prec),
        "recall": float(rec),
        "f1": float(f1),
        "auc": float(auc),
    }
    return vectorizer, clf, metrics


def _backup_current(version: str):
    if os.path.exists(MODEL_OUT_PATH):
        shutil.copy(MODEL_OUT_PATH, os.path.join(VERSIONS_DIR, f"logreg_{version}_previous.joblib"))
    if os.path.exists(MODEL_METRICS_PATH):
        shutil.copy(MODEL_METRICS_PATH, os.path.join(VERSIONS_DIR, f"logreg_{version}_previous_metrics.json"))


def _persist(version: str, vectorizer: TfidfVectorizer, clf: LogisticRegression, metrics: Dict):
    joblib.dump(vectorizer, TFIDF_PATH)
    joblib.dump(clf, MODEL_OUT_PATH)
    with open(MODEL_METRICS_PATH, "w") as f:
        json.dump(metrics, f, indent=4)

    joblib.dump(clf, os.path.join(VERSIONS_DIR, f"logreg_{version}.joblib"))
    with open(os.path.join(VERSIONS_DIR, f"logreg_{version}_metrics.json"), "w") as f:
        json.dump(metrics, f, indent=4)

    changelog_path = os.path.join(VERSIONS_DIR, "changelog.json")
    entry = {
        "version": version,
        "timestamp": datetime.utcnow().isoformat(),
        "metrics": metrics,
    }
    changelog: List[Dict] = []
    if os.path.exists(changelog_path):
        try:
            changelog = json.load(open(changelog_path))
        except Exception:
            changelog = []
    changelog.append(entry)
    with open(changelog_path, "w") as f:
        json.dump(changelog, f, indent=2)


def run_retrain(data_path: Optional[str] = None) -> Dict:
    path = data_path or os.getenv("DATA_PATH", DATA_PATH_DEFAULT)
    texts, labels = _load_dataset(path)
    texts, labels_list = _append_validated(texts, labels.tolist()) if len(labels) else _append_validated(texts, [])
    labels_array = np.array(labels_list)
    if not texts or len(texts) != len(labels_array) or len(set(labels_array)) < 1:
        raise RuntimeError("Not enough labeled data for retraining")

    version = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    _backup_current(version)
    vectorizer, clf, metrics = _train(texts, labels_array)
    _persist(version, vectorizer, clf, metrics)
    return {
        "version": version,
        "metrics": metrics,
    }


def list_versions() -> List[Dict]:
    changelog_path = os.path.join(VERSIONS_DIR, "changelog.json")
    if not os.path.exists(changelog_path):
        return []
    try:
        return json.load(open(changelog_path))
    except Exception:
        return []


def rollback(version: str) -> bool:
    model_path = os.path.join(VERSIONS_DIR, f"logreg_{version}.joblib")
    metrics_path = os.path.join(VERSIONS_DIR, f"logreg_{version}_metrics.json")
    if not os.path.exists(model_path) or not os.path.exists(metrics_path):
        return False
    shutil.copy(model_path, MODEL_OUT_PATH)
    shutil.copy(metrics_path, MODEL_METRICS_PATH)
    return True
