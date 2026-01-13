import joblib
import numpy as np
import pandas as pd
from pathlib import Path

# -----------------------------
# Paths
# -----------------------------
BASE_DIR = Path(__file__).resolve().parent
MODELS_DIR = BASE_DIR / "models"

EBM_PATH = MODELS_DIR / "ebm_risk.pkl"
NGB_PATH = MODELS_DIR / "ngboost_risk_bundle.pkl"

# -----------------------------
# FINAL RISK THRESHOLDS (REALISTIC)
# -----------------------------
EBM_ESCALATE_THRESHOLD = 0.25   # MEDIUM
EBM_HIGH_THRESHOLD = 0.45       # HIGH

# -----------------------------
# Blacklist
# -----------------------------
BLACKLIST_SET = {"BLK001", "BLK002", "BLACK123"}

def is_blacklisted(customer_id: str) -> bool:
    if not customer_id:
        return False
    return customer_id.strip().upper() in BLACKLIST_SET

# -----------------------------
# Load models
# -----------------------------
ebm_model = joblib.load(EBM_PATH)

ngb_bundle = joblib.load(NGB_PATH)
ngb_model = ngb_bundle["model"]
ngb_features = list(ngb_bundle["feature_columns"])

# -----------------------------
# Feature helpers
# -----------------------------
def _driver_age_band(age):
    if age < 25: return "18-24"
    if age < 35: return "25-34"
    if age < 45: return "35-44"
    if age < 55: return "45-54"
    if age < 65: return "55-64"
    return "65+"

def _vehicle_age_band(age):
    if age <= 3: return "0-3"
    if age <= 7: return "4-7"
    if age <= 12: return "8-12"
    if age <= 20: return "13-20"
    return "20+"

# -----------------------------
# Defaults
# -----------------------------
def _defaults(d):
    base = {
        "driver_age": 35,
        "driver_gender": "Male",
        "driver_occupation": "Private",
        "years_of_driving_experience": 10,
        "member_automobile_assoc_ceylon": 0,
        "has_previous_motor_policy": 0,
        "accidents_last_3_years": 0,
        "ncb_percentage": 0,
        "num_claims_within_1_year": 0,
        "vehicle_type": "Car",
        "vehicle_segment": "Sedan",
        "engine_capacity_cc": 1500,
        "fuel_type": "Petrol",
        "vehicle_age_years": 8,
        "vehicle_usage_type": "Private",
        "registration_district": "Colombo",
        "parking_type": "Garage",
        "has_lpg_conversion": 0,
        "customer_id": ""
    }
    for k, v in base.items():
        d.setdefault(k, v)
    return d

# -----------------------------
# Prepare data
# -----------------------------
def _prepare_df(inp):
    inp = _defaults(dict(inp))
    df = pd.DataFrame([inp])
    df["driver_age_band"] = df["driver_age"].apply(_driver_age_band)
    df["vehicle_age_band"] = df["vehicle_age_years"].apply(_vehicle_age_band)
    return df

def _prepare_for_ebm(df):
    X = df[ebm_model.feature_names_in_].copy()
    for c in X.columns:
        if X[c].dtype == "object":
            X[c] = X[c].astype(str)
    return X

def _prepare_for_ngb(df):
    X = pd.get_dummies(df, drop_first=False)
    for col in ngb_features:
        if col not in X.columns:
            X[col] = 0
    return X[ngb_features]

# -----------------------------
# NGBoost probability (SAFE)
# -----------------------------
def _ngb_prob(X):
    if hasattr(ngb_model, "predict_proba"):
        p = np.asarray(ngb_model.predict_proba(X))
        return float(p[0, -1])
    dist = ngb_model.pred_dist(X)
    return float(np.asarray(dist.probs)[0, -1])

# -----------------------------
# Risk label
# -----------------------------
def _risk_label(p):
    if p >= EBM_HIGH_THRESHOLD:
        return "HIGH"
    if p >= EBM_ESCALATE_THRESHOLD:
        return "MEDIUM"
    return "LOW"

# -----------------------------
# FINAL RISK FUNCTION
# -----------------------------
def calculate_risk(input_policy: dict) -> dict:
    df = _prepare_df(input_policy)

    ebm_prob = float(
        ebm_model.predict_proba(_prepare_for_ebm(df))[:, 1][0]
    )

    ngb_prob = _ngb_prob(_prepare_for_ngb(df))

    # ⭐ REAL UNDERWRITING LOGIC ⭐
    final_prob = ebm_prob

    # Escalate ONLY if both models agree
    if ngb_prob >= 0.80 and ebm_prob >= EBM_ESCALATE_THRESHOLD:
        final_prob = max(ebm_prob, ngb_prob)

    return {
        "risk_probability": final_prob,
        "risk_label": _risk_label(final_prob),
        "ebm_probability": ebm_prob,
        "ngboost_probability": ngb_prob
    }
