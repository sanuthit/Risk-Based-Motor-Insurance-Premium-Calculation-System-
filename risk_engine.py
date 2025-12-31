import joblib
import numpy as np
import pandas as pd
from pathlib import Path

# IMPORT PREMIUM LOGIC
from premium_rules import calculate_final_premium


# --------------------------------------------------
# Paths
# --------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
MODELS_DIR = BASE_DIR / "models"

EBM_PATH = MODELS_DIR / "ebm_risk.pkl"
NGB_PATH = MODELS_DIR / "ngboost_risk_bundle.pkl"


# --------------------------------------------------
# Thresholds (from your experiments – NOT guessed)
# --------------------------------------------------
EBM_ESCALATE_THRESHOLD = 0.155   # cost-based
EBM_HIGH_THRESHOLD     = 0.20    # F1-based


# --------------------------------------------------
# Load models
# --------------------------------------------------
ebm_model = joblib.load(EBM_PATH)

ngb_bundle = joblib.load(NGB_PATH)
ngb_model = ngb_bundle["model"]
ngb_features = ngb_bundle["feature_columns"]


# --------------------------------------------------
# Get EBM trained feature list (CRITICAL)
# --------------------------------------------------
if hasattr(ebm_model, "feature_names_in_"):
    ebm_features = list(ebm_model.feature_names_in_)
elif hasattr(ebm_model, "feature_names_"):
    ebm_features = list(ebm_model.feature_names_)
else:
    raise RuntimeError("Cannot find feature names in EBM model.")


# --------------------------------------------------
# Age band rules (MUST MATCH training dataset)
# --------------------------------------------------
def make_driver_age_band(age):
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


def make_vehicle_age_band(v_age):
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
def to_dataframe(policy_dict):
    return pd.DataFrame([policy_dict])


def add_engineered_features(df):
    # Guard checks
    if "driver_age" not in df.columns:
        raise ValueError("Missing required field: driver_age")
    if "vehicle_age_years" not in df.columns:
        raise ValueError("Missing required field: vehicle_age_years")

    # Create bands
    df["driver_age_band"] = df["driver_age"].apply(make_driver_age_band)
    df["vehicle_age_band"] = df["vehicle_age_years"].apply(make_vehicle_age_band)
    return df


def prepare_for_ebm(df):
    missing = [c for c in ebm_features if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required EBM features: {missing}")
    return df[ebm_features]


def encode_for_ngboost(df):
    X = pd.get_dummies(df, drop_first=False)
    X = X.reindex(columns=ngb_features, fill_value=0)
    return X


# --------------------------------------------------
# MAIN RISK + PREMIUM FUNCTION
# --------------------------------------------------
def calculate_risk(policy):
    """
    Input : policy data (dict)
    Output: risk + premium breakdown
    """

    # 1) Input → DataFrame
    df = to_dataframe(policy)

    # 2) Feature engineering for EBM (bands)
    df = add_engineered_features(df)

    # 3) EBM risk prediction
    X_ebm = prepare_for_ebm(df)
    ebm_prob = float(ebm_model.predict_proba(X_ebm)[0, 1])

    # 4) Risk label using EBM (for workflow/decision)
    if ebm_prob >= EBM_HIGH_THRESHOLD:
        risk_label = "HIGH"
    elif ebm_prob >= EBM_ESCALATE_THRESHOLD:
        risk_label = "MEDIUM"
    else:
        risk_label = "LOW"

    escalate = ebm_prob >= EBM_ESCALATE_THRESHOLD

    # Result skeleton
    result = {
        "ebm_risk_probability": round(ebm_prob, 4),
        "risk_label": risk_label,
        "escalate_to_ngboost": bool(escalate),

        "ngboost_risk_probability": None,
        "ngboost_uncertainty": None,

        "driver_age_band": df["driver_age_band"].iloc[0],
        "vehicle_age_band": df["vehicle_age_band"].iloc[0],

        # will be filled after choosing pricing probability
        "pricing_model_used": None,
        "pricing_probability": None,
        "risk_percent_for_pricing": None,
        "premium_breakdown": None
    }

    # 5) NGBoost (only if escalated)
    if escalate:
        X_ngb = encode_for_ngboost(df)
        dist = ngb_model.pred_dist(X_ngb)
        params = dist.params if hasattr(dist, "params") else dist.params_

        p1 = float(np.asarray(params["p1"]).reshape(-1)[0])  # claim probability
        uncertainty = float(np.sqrt(p1 * (1 - p1)))

        result["ngboost_risk_probability"] = round(p1, 4)
        result["ngboost_uncertainty"] = round(uncertainty, 4)

    # 6) Choose probability for PREMIUM (your required rule)
    if result["ngboost_risk_probability"] is not None:
        pricing_prob = float(result["ngboost_risk_probability"])
        pricing_model_used = "NGBoost"
    else:
        pricing_prob = float(result["ebm_risk_probability"])
        pricing_model_used = "EBM"

    risk_percent_for_pricing = pricing_prob * 100.0

    result["pricing_model_used"] = pricing_model_used
    result["pricing_probability"] = round(pricing_prob, 4)
    result["risk_percent_for_pricing"] = round(risk_percent_for_pricing, 2)

    # 7) Premium calculation (RULE BASED)
    # Prefer using base_premium from input policy if provided
    base_premium = float(policy.get("base_premium", 45000))

    premium_breakdown = calculate_final_premium(
        base_premium=base_premium,
        risk_percent=risk_percent_for_pricing,
        ncb_percentage=float(policy.get("ncb_percentage", 0)),
        other_discount=float(policy.get("other_discount", 0))
    )

    result["premium_breakdown"] = premium_breakdown

    return result


# --------------------------------------------------
# Example run
# --------------------------------------------------
if __name__ == "__main__":

    sample_policy = {
        "driver_age": 23,
        "driver_gender": "Male",
        "driver_occupation": "Private",
        "years_of_driving_experience": 2,
        "member_automobile_assoc_ceylon": 0,
        "has_previous_motor_policy": 0,
        "ncb_percentage": 0,
        "accidents_last_3_years": 2,

        "vehicle_type": "Car",
        "vehicle_segment": "Hatchback",
        "engine_capacity_cc": 1800,
        "fuel_type": "Petrol",
        "vehicle_age_years": 18,
        "vehicle_usage_type": "Commercial",
        "registration_district": "Colombo",
        "parking_type": "Road",
        "has_lpg_conversion": 1,

        "vehicle_make": "TOYOTA",
        "vehicle_model": "Starlet",
        "images_uploaded": 0,
        "inspection_report_uploaded": 0,
        "registration_book_available": 0,
        "rebate_within_company_limits": 0,
        "is_existing_customer": 0,
        "is_blacklisted_customer": 1,

        "coverage_type": "Third Party",
        "approx_market_value": 2200000,
        "sum_insured": 2000000,
        "num_claims_within_1_year": 1,
        "total_claim_amount_within_1_year": 450000,

        # optional pricing inputs
        "base_premium": 45000,
        "other_discount": 0
    }

    output = calculate_risk(sample_policy)

    print("\nFINAL OUTPUT")
    for k, v in output.items():
        if k == "premium_breakdown" and isinstance(v, dict):
            print("premium_breakdown:")
            for pk, pv in v.items():
                print(f"  {pk}: {pv}")
        else:
            print(f"{k}: {v}")
