import os
import numpy as np
import xgboost as xgb


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

MODEL_PATH = os.path.join(
    BASE_DIR,
    "models",
    "xgboost_fusion_model.json"
)

THRESHOLD = 0.30


print("Loading XGBoost model...")
print(f"Model path: {MODEL_PATH}")
print(f"Prediction threshold: {THRESHOLD}")


if not os.path.exists(MODEL_PATH):
    raise FileNotFoundError(
        f"XGBoost model not found:\n{MODEL_PATH}"
    )


model = xgb.XGBClassifier()

model.load_model(MODEL_PATH)

print("XGBoost model loaded successfully.")


def predict(features):
    """
    Production prediction.

    IMPORTANT:
    This function receives ONLY extracted features.
    It does NOT receive or use actual_label.
    """

    if features is None:
        raise ValueError("Features cannot be None.")

    features = np.asarray(
        features,
        dtype=np.float32
    )

    if features.ndim == 1:
        features = features.reshape(1, -1)

    expected_features = model.n_features_in_

    if features.shape[1] != expected_features:
        raise ValueError(
            f"Feature dimension mismatch. "
            f"Expected {expected_features}, "
            f"received {features.shape[1]}."
        )

    probabilities = model.predict_proba(features)

    fake_probability = float(
        probabilities[0][1]
    )

    real_probability = float(
        probabilities[0][0]
    )

    # IMPORTANT:
    # 0.30 is your experimentally selected threshold.
    predicted_label = (
        "FAKE"
        if fake_probability >= THRESHOLD
        else "REAL"
    )

    confidence = (
        fake_probability
        if predicted_label == "FAKE"
        else real_probability
    )

    return {
        "predicted_label": predicted_label,
        "fake_probability": fake_probability,
        "real_probability": real_probability,
        "confidence": float(confidence),
        "threshold": THRESHOLD
    }