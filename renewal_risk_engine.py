import joblib
import pandas as pd

from premium_rules import calculate_final_premium

MODEL_PATH = "models/ngboost_risk_bundle.pkl"


class RenewalRiskEngine:
    def __init__(self, model_path: str = MODEL_PATH):
        bundle = joblib.load(model_path)

        self.model = bundle["model"]
        self.features = bundle["feature_columns"]

    def predict_expected_claim(self, policy_features: dict) -> float:
        """
        Predict expected claim amount using NGBoost.
        """
        X = pd.DataFrame([policy_features])

        # Ensure all required features exist (fill missing with 0)
        for col in self.features:
            if col not in X.columns:
                X[col] = 0

        X = X[self.features]

        pred = self.model.pred_dist(X)
        return float(pred.mean()[0])

    def risk_score_from_claim(self, expected_claim: float) -> float:
        """
        Convert expected claim to 0–100 risk score.
        NOTE: change max_reasonable_claim to match your portfolio.
        """
        max_reasonable_claim = 1_500_000
        score01 = min(max(expected_claim, 0) / max_reasonable_claim, 1.0)
        return round(score01 * 100, 2)

    def evaluate_policy(
        self,
        policy_features: dict,
        sum_insured: float,
        ncb_rate: float = 0.0
    ) -> dict:
        """
        Full pipeline: expected claim -> risk score -> premium breakdown
        """
        expected_claim = self.predict_expected_claim(policy_features)
        risk_score = self.risk_score_from_claim(expected_claim)

        premium_breakdown = calculate_final_premium(
            sum_insured=float(sum_insured),
            expected_claim=float(expected_claim),
            ncb_rate=float(ncb_rate)
        )

        return {
            "expected_claim_amount": round(expected_claim, 2),
            "risk_score": risk_score,
            "premium_breakdown": premium_breakdown
        }


_engine = RenewalRiskEngine()

def evaluate_policy(policy_features: dict, sum_insured: float, ncb_rate: float = 0.0) -> dict:
    return _engine.evaluate_policy(policy_features, sum_insured, ncb_rate)
