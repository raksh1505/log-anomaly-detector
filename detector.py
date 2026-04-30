import re
import json
import numpy as np
from datetime import datetime
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler


# ─── Log Parsing ────────────────────────────────────────────────────────────

LOG_PATTERN = re.compile(
    r'(?P<timestamp>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})'
    r'.*?(?P<level>DEBUG|INFO|WARNING|ERROR|CRITICAL)'
    r'.*?(?P<message>.+)'
)

LEVEL_SCORES = {"DEBUG": 0, "INFO": 1, "WARNING": 2, "ERROR": 3, "CRITICAL": 4}


def parse_log_line(line: str) -> dict | None:
    match = LOG_PATTERN.search(line)
    if not match:
        return None
    return {
        "timestamp": match.group("timestamp"),
        "level": match.group("level"),
        "message": match.group("message").strip(),
        "raw": line.strip()
    }


def extract_features(log: dict) -> list[float]:
    msg = log["message"]
    return [
        LEVEL_SCORES.get(log["level"], 0),          # severity
        len(msg),                                    # message length
        msg.count(" "),                              # word count proxy
        1 if re.search(r'\d{3}', msg) else 0,       # contains status code
        1 if re.search(r'timeout|refused|fail', msg, re.I) else 0,  # error keywords
        1 if re.search(r'exception|traceback|error', msg, re.I) else 0,  # exception keywords
        1 if re.search(r'\d+ms|\d+s\b', msg) else 0,  # latency mention
    ]


# ─── Anomaly Detection ───────────────────────────────────────────────────────

class LogAnomalyDetector:
    def __init__(self, contamination: float = 0.1):
        self.model = IsolationForest(contamination=contamination, random_state=42)
        self.scaler = StandardScaler()
        self.trained = False

    def fit(self, logs: list[dict]):
        features = [extract_features(log) for log in logs]
        X = self.scaler.fit_transform(features)
        self.model.fit(X)
        self.trained = True

    def predict(self, logs: list[dict]) -> list[dict]:
        if not self.trained:
            raise RuntimeError("Model not trained. Call fit() first.")

        features = [extract_features(log) for log in logs]
        X = self.scaler.transform(features)
        scores = self.model.decision_function(X)   # lower = more anomalous
        predictions = self.model.predict(X)         # -1 = anomaly, 1 = normal

        results = []
        for log, pred, score in zip(logs, predictions, scores):
            results.append({
                **log,
                "is_anomaly": pred == -1,
                "anomaly_score": round(float(score), 4)
            })
        return results


# ─── Batch Processing ────────────────────────────────────────────────────────

def analyze_log_file(filepath: str, contamination: float = 0.1) -> list[dict]:
    with open(filepath, "r") as f:
        lines = f.readlines()

    logs = [parsed for line in lines if (parsed := parse_log_line(line))]
    if not logs:
        return []

    detector = LogAnomalyDetector(contamination=contamination)
    detector.fit(logs)
    return detector.predict(logs)


def analyze_log_text(text: str, contamination: float = 0.1) -> list[dict]:
    lines = text.strip().split("\n")
    logs = [parsed for line in lines if (parsed := parse_log_line(line))]
    if not logs:
        return []

    detector = LogAnomalyDetector(contamination=contamination)
    detector.fit(logs)
    return detector.predict(logs)
