from flask import Flask, render_template, request
from renewal_risk_engine import RenewalRiskEngine

app = Flask(__name__)

engine = RenewalRiskEngine()


@app.route("/", methods=["GET"])
def home():
    return render_template("index.html")


@app.route("/predict", methods=["POST"])
def predict():
    # --- Read basic inputs ---
    sum_insured = float(request.form.get("sum_insured", 0) or 0)
    ncb_rate = float(request.form.get("ncb_rate", 0) or 0)  # % or decimal? depends on your premium_rules

    # --- Build policy_features dict from form ---
    # IMPORTANT: These keys MUST match engine.features (training columns).
    # We'll collect everything from the form except sum_insured & ncb_rate.
    policy_features = {}

    for k, v in request.form.items():
        if k in ["sum_insured", "ncb_rate"]:
            continue

        # Try numeric conversion; otherwise keep as string
        try:
            policy_features[k] = float(v)
        except:
            policy_features[k] = v

    # --- Evaluate policy ---
    result = engine.evaluate_policy(
        policy_features=policy_features,
        sum_insured=sum_insured,
        ncb_rate=ncb_rate
    )

    return render_template("index.html", result=result)


if __name__ == "__main__":
    app.run(debug=True)
