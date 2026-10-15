
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report

np.random.seed(42)

n = 5000

data = pd.DataFrame({
    "temperature": np.random.normal(70, 15, n).clip(20, 150),
    "vibration": np.random.normal(0.7, 0.35, n).clip(0.01, 5),
    "pressure": np.random.normal(30, 8, n).clip(5, 60),
    "runtime": np.random.randint(100, 10001, n)
})

# Synthetic demonstration rules; replace with real labeled data
# when available.
risk_score = (
    (data["temperature"] > 90).astype(int)
    + (data["vibration"] > 1.2).astype(int)
    + (data["pressure"] > 40).astype(int)
    + (data["runtime"] > 8000).astype(int)
)

data["failure"] = (risk_score >= 2).astype(int)

features = [
    "temperature",
    "vibration",
    "pressure",
    "runtime"
]

X = data[features]
y = data["failure"]

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.2,
    random_state=42,
    stratify=y
)

model = RandomForestClassifier(
    n_estimators=200,
    random_state=42,
    class_weight="balanced",
    min_samples_leaf=2
)

model.fit(X_train, y_train)

predictions = model.predict(X_test)

print("Test accuracy:",
      round(accuracy_score(y_test, predictions) * 100, 2), "%")

print(classification_report(
    y_test, predictions, zero_division=0
))

model_path = Path(__file__).parent / "failure_model.pkl"
joblib.dump(model, model_path)

print("Model saved to:", model_path.resolve())
