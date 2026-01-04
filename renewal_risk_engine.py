# risk_engine.py

import joblib
import numpy as np
import pandas as pd

from premium_rules import calculate_final_premium

MODEL_PATH = "models/ngboost_risk_bundle.pkl"


class RenewalRiskEngine:
    def __init__(self):
        bundle = joblib.load(MODEL_PATH)
        self.model = bundle["model"]
        self.features = bundle["feature_columns"]

    def predict_expected_claim(self, policy_features: dict) -> float:
        """
        Predict expected claim amount using NGBoost
        """
        X = pd.DataFrame([policy_features])[self.features]
        pred = self.model.pred_dist(X)
        return float(pred.mean()[0])

    def risk_score_from_claim(self, expected_claim: float) -> float:
        """
        Normalize expected claim into 0–100 risk score
        """
        max_reasonable_claim = 1_500_000
        score = min(expected_claim / max_reasonable_claim, 1.0)
        return round(score * 100, 2)

    def evaluate_policy(
        self,
        policy_features: dict,
        sum_insured: float,
        ncb_rate: float = 0.0
    ) -> dict:
        """
        Full policy evaluation pipeline
        """

        expected_claim = self.predict_expected_claim(policy_features)
        risk_score = self.risk_score_from_claim(expected_claim)

        premium = calculate_final_premium(
            sum_insured=sum_insured,
            expected_claim=expected_claim,
            ncb_rate=ncb_rate
        )

        return {
            "expected_claim_amount": round(expected_claim, 2),
            "risk_score": risk_score,
            "premium_breakdown": premium
        }
