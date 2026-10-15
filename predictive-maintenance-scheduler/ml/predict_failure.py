from pathlib import Path
import joblib
import pandas as pd

MODEL_PATH = Path(__file__).parent / "failure_model.pkl"
model = joblib.load(MODEL_PATH)


def predict_failure(temperature, vibration, pressure, runtime):
    features = pd.DataFrame([{
        "temperature": temperature,
        "vibration": vibration,
        "pressure": pressure,
        "runtime": runtime
    }])

    prediction = int(model.predict(features)[0])
    probabilities = model.predict_proba(features)[0]

    return {
        "failure_prediction": prediction,
        "failure_risk_percent": round(
            float(probabilities[1]) * 100, 2
        )
    }


if __name__ == "__main__":
    print(predict_failure(85, 0.8, 30, 1200))