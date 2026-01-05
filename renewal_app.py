from flask import Flask, render_template, request
from renewal_risk_engine import evaluate_policy

app = Flask(__name__)


@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")


@app.route("/predict", methods=["POST"])
def predict():
    policy_features = {
        "claims_last_1_year": float(request.form["claims_last_1_year"]),
        "claims_last_3_years": float(request.form["claims_last_3_years"]),
        "largest_claim_amount_last_1_year": float(request.form["largest_claim_amount_last_1_year"]),
        "had_major_claim_last_1_year": int(request.form["had_major_claim_last_1_year"]),
        "small_frequent_claims_flag": int(request.form["small_frequent_claims_flag"]),
        "years_since_last_claim": float(request.form["years_since_last_claim"]),
    }

    sum_insured = float(request.form["sum_insured"])

    result = evaluate_policy(policy_features, sum_insured)

    return render_template("index.html", result=result)
    

if __name__ == "__main__":
    app.run(debug=True)
