import joblib
import numpy as np
import pandas as pd
from pathlib import Path


# --------------------------------------------------
# Paths
# --------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
MODELS_DIR = BASE_DIR / "models"

EBM_PATH = MODELS_DIR / "ebm_risk.pkl"
NGB_PATH = MODELS_DIR / "ngboost_risk_bundle.pkl"


# --------------------------------------------------
# Thresholds (use your chosen ones – not guessed)
# --------------------------------------------------
EBM_ESCALATE_THRESHOLD = 0.155   # cost-based threshold you tested
EBM_HIGH_THRESHOLD     = 0.20    # F1-based threshold you tested


# --------------------------------------------------
# Load models
# --------------------------------------------------
ebm_model = joblib.load(EBM_PATH)

ngb_bundle = joblib.load(NGB_PATH)
ngb_model = ngb_bundle["model"]
ngb_features = ngb_bundle["feature_columns"]


# --------------------------------------------------
# Get EBM trained feature list (CRITICAL FIX)
# --------------------------------------------------
if hasattr(ebm_model, "feature_names_in_"):
    ebm_features = list(ebm_model.feature_names_in_)
elif hasattr(ebm_model, "feature_names_"):
    ebm_features = list(ebm_model.feature_names_)
else:
    raise RuntimeError(
        "Cannot find feature names in EBM model. "
        "Re-save EBM as a bundle with feature list."
    )


# --------------------------------------------------
# Age banding rules (MUST MATCH your training labels)
# Based on your screenshot: driver_age_band uses "60+"
# and vehicle_age_band uses "13+"
# --------------------------------------------------
def make_driver_age_band(age) -> str:
    age = float(age)
    if age < 25:
        return "18_24"
    elif age < 35:
        return "25_34"
    elif age < 45:
        return "35_44"
    elif age < 60:
        return "45_59"
    else:
        return "60+"


def make_vehicle_age_band(v_age) -> str:
    v_age = float(v_age)
    if v_age <= 3:
        return "0_3"
    elif v_age <= 7:
        return "4_7"
    elif v_age <= 12:
        return "8_12"
    else:
        return "13+"


# --------------------------------------------------
# Helpers
# --------------------------------------------------
def to_dataframe(policy_dict: dict) -> pd.DataFrame:
    """Convert input dict → 1-row DataFrame."""
    return pd.DataFrame([policy_dict])


def add_required_engineered_features(df_row: pd.DataFrame) -> pd.DataFrame:
    """
    Ensure engineered features exist for inference.
    EBM was trained with age bands, so we must generate them here.
    """
    # driver_age_band
    if "driver_age_band" not in df_row.columns:
        if "driver_age" not in df_row.columns:
            raise ValueError("Missing 'driver_age' (needed to compute driver_age_band)")
        df_row["driver_age_band"] = df_row["driver_age"].apply(make_driver_age_band)

    # vehicle_age_band
    if "vehicle_age_band" not in df_row.columns:
        if "vehicle_age_years" not in df_row.columns:
            raise ValueError("Missing 'vehicle_age_years' (needed to compute vehicle_age_band)")
        df_row["vehicle_age_band"] = df_row["vehicle_age_years"].apply(make_vehicle_age_band)

    return df_row


def prepare_for_ebm(df_row: pd.DataFrame) -> pd.DataFrame:
    """
    Select only the features EBM was trained on.
    If a required feature is missing, raise clear error.
    """
    missing = [c for c in ebm_features if c not in df_row.columns]
    if missing:
        raise ValueError(f"Missing required EBM features: {missing}")

    return df_row[ebm_features]


def encode_for_ngboost(df_row: pd.DataFrame) -> pd.DataFrame:
    """
    One-hot encode and align to the saved NGBoost feature columns.
    """
    X = pd.get_dummies(df_row, drop_first=False)
    X = X.reindex(columns=ngb_features, fill_value=0)
    return X


# --------------------------------------------------
# MAIN RISK CALCULATION FUNCTION
# --------------------------------------------------
def calculate_risk(policy: dict) -> dict:
    """
    Input : policy data as dictionary
    Output: EBM risk + label + optional NGBoost risk & uncertainty
    """

    df = to_dataframe(policy)

    # ✅ create age bands automatically (so user doesn't need to enter them)
    df = add_required_engineered_features(df)

    # ---- 1) EBM prediction (primary) ----
    X_ebm = prepare_for_ebm(df)
    ebm_prob = float(ebm_model.predict_proba(X_ebm)[0, 1])

    # ---- 2) Risk label & escalation ----
    if ebm_prob >= EBM_HIGH_THRESHOLD:
        risk_label = "HIGH"
    elif ebm_prob >= EBM_ESCALATE_THRESHOLD:
        risk_label = "MEDIUM"
    else:
        risk_label = "LOW"

    escalate = ebm_prob >= EBM_ESCALATE_THRESHOLD

    result = {
        "ebm_risk_probability": round(ebm_prob, 4),
        "risk_label": risk_label,
        "escalate_to_ngboost": bool(escalate),
        "ngboost_risk_probability": None,
        "ngboost_uncertainty": None,
        # helpful debug fields (optional to show in UI)
        "driver_age_band": df["driver_age_band"].iloc[0],
        "vehicle_age_band": df["vehicle_age_band"].iloc[0],
    }

    # ---- 3) NGBoost prediction (only if escalated) ----
    if escalate:
        X_ngb = encode_for_ngboost(df)

        dist = ngb_model.pred_dist(X_ngb)

        # Your NGBoost returns p0/p1 (NOT p)
        params = dist.params if hasattr(dist, "params") else dist.params_
        p1 = float(np.asarray(params["p1"]).reshape(-1)[0])  # claim probability

        # simple uncertainty proxy
        uncertainty = float(np.sqrt(p1 * (1 - p1)))

        result["ngboost_risk_probability"] = round(p1, 4)
        result["ngboost_uncertainty"] = round(uncertainty, 4)

    return result


# --------------------------------------------------
# Example run
# --------------------------------------------------
if __name__ == "__main__":

    # user only enters raw ages; bands will be auto-generated
    sample_policy = {
    # Driver risk
    "driver_age": 23,
    "driver_gender": "Male",
    "driver_occupation": "Private",
    "years_of_driving_experience": 2,
    "member_automobile_assoc_ceylon": 0,
    "has_previous_motor_policy": 0,
    "ncb_percentage": 0,
    "accidents_last_3_years": 2,

    # Vehicle risk
    "vehicle_type": "Car",
    "vehicle_segment": "Hatchback",
    "engine_capacity_cc": 1800,
    "fuel_type": "Petrol",
    "vehicle_age_years": 18,
    "vehicle_usage_type": "Commercial",
    "registration_district": "Colombo",
    "parking_type": "Road",
    "has_lpg_conversion": 1,

    # Compliance / history
    "vehicle_make": "TOYOTA",
    "vehicle_model": "Starlet",
    "images_uploaded": 0,
    "inspection_report_uploaded": 0,
    "registration_book_available": 0,
    "rebate_within_company_limits": 0,
    "is_existing_customer": 0,
    "is_blacklisted_customer": 1,

    # Policy / claims
    "coverage_type": "Third Party",
    "approx_market_value": 2200000,
    "sum_insured": 2000000,
    "num_claims_within_1_year": 1,
    "total_claim_amount_within_1_year": 450000
}


    print("\nEBM expects these features (debug):")
    print(ebm_features)

    output = calculate_risk(sample_policy)

    print("\nFINAL RISK OUTPUT")
    for k, v in output.items():
        print(f"{k}: {v}")
