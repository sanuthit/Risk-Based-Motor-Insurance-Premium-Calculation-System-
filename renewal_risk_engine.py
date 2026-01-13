import joblib
import pandas as pd

from renewal_premium_rules import calculate_final_premium

MODEL_PATH = "models/ngboost_renewal_bundle.pkl"


class RenewalRiskEngine:
    def __init__(self, model_path: str = MODEL_PATH):
        bundle = joblib.load(model_path)
        self.model = bundle["model"]
        self.features = bundle["feature_columns"]

    def predict_expected_claim(self, policy_features: dict) -> float:
        X = pd.DataFrame([policy_features])

        # Fill missing features with 0
        for col in self.features:
            if col not in X.columns:
                X[col] = 0

        X = X[self.features]

        dist = self.model.pred_dist(X)
        return float(dist.mean()[0])

    def risk_score_from_claim(self, expected_claim: float) -> float:
        MAX_REASONABLE_CLAIM = 1_500_000
        score = min(max(expected_claim, 0) / MAX_REASONABLE_CLAIM, 1.0)
        return round(score * 100, 2)

    def evaluate_policy(self, policy_features: dict, sum_insured: float) -> dict:
        expected_claim = self.predict_expected_claim(policy_features)
        risk_score = self.risk_score_from_claim(expected_claim)

        premium = calculate_final_premium(
            sum_insured=float(sum_insured),
            expected_claim=float(expected_claim)
        )

        return {
            "expected_claim_amount": round(expected_claim, 2),
            "risk_score": risk_score,
            "premium_breakdown": premium,
            "total_premium": premium["total_premium"]
        }


_engine = RenewalRiskEngine()

def evaluate_policy(policy_features: dict, sum_insured: float) -> dict:
    return _engine.evaluate_policy(policy_features, sum_insured)
