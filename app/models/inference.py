import os
import json
import time
from datetime import datetime
from typing import Optional, Tuple

import numpy as np
import re
import joblib

# Optional tensorflow import guarded at runtime
TF_AVAILABLE = False
try:
    import tensorflow as tf  # type: ignore
    TF_AVAILABLE = True
except Exception:
    TF_AVAILABLE = False

from sklearn.linear_model import LogisticRegression


DATA_PATH_DEFAULT = "fake_job_postings.csv"
TFIDF_PATH = os.path.join("m1_outputs", "tfidf_vectorizer.pkl")
LOGREG_PATH = os.path.join("m2_outputs", "logreg_best.joblib")
LOGREG_METRICS = os.path.join("m2_outputs", "logreg_metrics.json")
BILSTM_PATH = os.path.join("m2_outputs", "bilstm_model.keras")
TOKENIZER_PATH = os.path.join("m2_outputs", "tokenizer.pkl")
BILSTM_METRICS = os.path.join("m2_outputs", "bilstm_metrics.json")
RF_METRICS = os.path.join("m2_outputs", "random_forest_metrics.json")


def basic_clean(text: str) -> str:
    text = str(text).lower()
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"http\S+|www\.\S+", " ", text)
    text = re.sub(r"[^a-z\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


class ModelService:
    def __init__(self) -> None:
        self.ready: bool = False
        self.model_name: Optional[str] = None
        self.vectorizer = None
        self.clf = None
        self.dl_model = None
        self.tokenizer = None
        self.metrics: dict = {}
        self.last_loaded: Optional[str] = None

    def _load_tfidf(self) -> None:
        if os.path.exists(TFIDF_PATH):
            self.vectorizer = joblib.load(TFIDF_PATH)
        else:
            self.vectorizer = None

    def _load_logreg(self) -> bool:
        if os.path.exists(LOGREG_PATH):
            self.clf = joblib.load(LOGREG_PATH)
            self.model_name = "LogisticRegression"
            if os.path.exists(LOGREG_METRICS):
                try:
                    self.metrics = json.load(open(LOGREG_METRICS))
                except Exception:
                    self.metrics = {"model": "LogisticRegression"}
            return True
        return False

    def _load_bilstm(self) -> bool:
        if os.path.exists(BILSTM_PATH) and os.path.exists(TOKENIZER_PATH) and TF_AVAILABLE:
            try:
                self.dl_model = tf.keras.models.load_model(BILSTM_PATH)
                import pickle
                with open(TOKENIZER_PATH, "rb") as f:
                    self.tokenizer = pickle.load(f)
                self.model_name = "BiLSTM"
                if os.path.exists(BILSTM_METRICS):
                    self.metrics = json.load(open(BILSTM_METRICS))
                return True
            except Exception:
                return False
        return False

    def _fallback_train(self) -> bool:
        # Train a quick logistic regression if artifacts are missing.
        # Prefer real dataset if available; otherwise use a tiny synthetic dataset for demo readiness.
        data_path = os.getenv("DATA_PATH", DATA_PATH_DEFAULT)
        try:
            texts = []
            y = None
            if os.path.exists(data_path):
                import pandas as pd
                from sklearn.model_selection import train_test_split
                df = pd.read_csv(data_path, low_memory=False)
                if "description" in df.columns and "fraudulent" in df.columns:
                    texts = df["description"].fillna("").apply(basic_clean).tolist()
                    y = df["fraudulent"].astype(int).values
            # If no real data, synthesize a tiny demo dataset
            if not texts:
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
                texts = [basic_clean(t) for t in synth_real + synth_fake]
                y = np.array([0]*len(synth_real) + [1]*len(synth_fake))

            from sklearn.feature_extraction.text import TfidfVectorizer
            if self.vectorizer is None:
                self.vectorizer = TfidfVectorizer(token_pattern=r"(?u)\b[a-zA-Z]{2,}\b", stop_words='english', max_features=1000)
            X = self.vectorizer.fit_transform(texts)

            from sklearn.model_selection import train_test_split
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42, stratify=y if len(set(y))>1 else None
            )
            clf = LogisticRegression(class_weight="balanced", max_iter=2000)
            clf.fit(X_train, y_train)
            self.clf = clf
            self.model_name = "LogisticRegression (fallback)"
            self.metrics = {"model": self.model_name}
            return True
        except Exception:
            return False

    def load(self) -> None:
        self._load_tfidf()

        # Prefer Logistic Regression artifacts; else BiLSTM; else fallback
        loaded = self._load_logreg()
        if not loaded:
            loaded = self._load_bilstm()
        if not loaded:
            loaded = self._fallback_train()

        self.ready = bool(loaded)
        self.last_loaded = datetime.utcnow().isoformat()

    def info(self) -> dict:
        vec_info = {}
        if self.vectorizer is not None:
            try:
                vec_info = {
                    "type": type(self.vectorizer).__name__,
                    "max_features": getattr(self.vectorizer, "max_features", None),
                }
            except Exception:
                vec_info = {"type": "unknown"}
        return {
            "model": self.model_name,
            "metrics": self.metrics,
            "vectorizer": vec_info,
            "last_loaded": self.last_loaded,
        }

    def _predict_sklearn(self, text: str) -> Tuple[int, float]:
        if self.vectorizer is None or self.clf is None:
            raise ValueError("Classifier or vectorizer not available")
        clean = basic_clean(text)
        X = self.vectorizer.transform([clean])
        if hasattr(self.clf, "predict_proba"):
            prob = float(self.clf.predict_proba(X)[0][1])
        else:
            # Decision function fallback approximated to probability range
            decision = float(self.clf.decision_function(X)[0])
            prob = 1 / (1 + np.exp(-decision))
        label = int(prob >= 0.5)
        return label, prob

    def _predict_bilstm(self, text: str) -> Tuple[int, float]:
        if not TF_AVAILABLE or self.dl_model is None or self.tokenizer is None:
            raise ValueError("DL model not available")
        clean = basic_clean(text)
        seq = self.tokenizer.texts_to_sequences([clean])
        from tensorflow.keras.preprocessing.sequence import pad_sequences
        X = pad_sequences(seq, maxlen=self.dl_model.input_shape[1])
        prob = float(self.dl_model.predict(X, verbose=0).ravel()[0])
        label = int(prob >= 0.5)
        return label, prob

    def predict(self, text: str) -> Tuple[int, float]:
        if not text or len(text.strip()) < 10:
            raise ValueError("Description too short")
        start = time.perf_counter()
        if self.model_name and self.model_name.startswith("BiLSTM"):
            label, prob = self._predict_bilstm(text)
        else:
            label, prob = self._predict_sklearn(text)
        _ = time.perf_counter() - start
        return label, prob
