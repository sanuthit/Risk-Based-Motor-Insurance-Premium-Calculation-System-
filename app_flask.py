import re
from flask import Flask, render_template, request
from risk_engine import calculate_risk, is_blacklisted
from premium_rules import calculate_final_premium

app = Flask(__name__)

NIC_OLD = re.compile(r"^\d{9}[vVxX]$")
NIC_NEW = re.compile(r"^\d{12}$")

def is_valid_nic(nic: str) -> bool:
    if not nic:
        return False
    nic = nic.strip()
    return bool(NIC_OLD.match(nic) or NIC_NEW.match(nic))

def clamp_int(x, lo, hi, default):
    try:
        x = int(x)
        return max(lo, min(hi, x))
    except Exception:
        return default

def clamp_float(x, lo, hi, default):
    try:
        x = float(x)
        return max(lo, min(hi, x))
    except Exception:
        return default

@app.get("/")
def register_page():
    return render_template("register.html", errors={}, result=None, premium=None, form={})

@app.post("/calculate")
def calculate():
    errors = {}
    form = request.form.to_dict(flat=True)

    # ---------------- CUSTOMER ----------------
    full_name = (form.get("full_name") or "").strip()
    nic = (form.get("nic") or "").strip()
    customer_id = (form.get("customer_id") or "").strip()

    if len(full_name) < 3:
        errors["full_name"] = "Name is required (min 3 characters)."
    if not is_valid_nic(nic):
        errors["nic"] = "Invalid NIC. Use 12 digits OR 9 digits + V/X."
    if customer_id and is_blacklisted(customer_id):
        errors["customer_id"] = "Customer is BLACKLISTED."

    # ---------------- RISK INPUTS ----------------
    driver_age = clamp_int(form.get("driver_age"), 18, 90, 35)
    MIN_LICENSE_AGE = 18
    max_exp = max(driver_age - MIN_LICENSE_AGE, 0)

    years_of_driving_experience = clamp_int(form.get("years_of_driving_experience"), 0, 70, 10)
    years_of_driving_experience = min(years_of_driving_experience, max_exp)

    input_policy = {
        "driver_age": driver_age,
        "driver_gender": form.get("driver_gender", "Male"),
        "driver_occupation": form.get("driver_occupation", "Private"),
        "years_of_driving_experience": years_of_driving_experience,
        "member_automobile_assoc_ceylon": clamp_int(form.get("member_automobile_assoc_ceylon"), 0, 1, 0),

        "has_previous_motor_policy": clamp_int(form.get("has_previous_motor_policy"), 0, 1, 0),
        "accidents_last_3_years": clamp_int(form.get("accidents_last_3_years"), 0, 10, 0),
        "ncb_percentage": clamp_int(form.get("ncb_percentage"), 0, 70, 0),
        "num_claims_within_1_year": clamp_int(form.get("num_claims_within_1_year"), 0, 10, 0),

        "vehicle_type": form.get("vehicle_type", "Car"),
        "vehicle_segment": form.get("vehicle_segment", "Sedan"),
        "engine_capacity_cc": clamp_int(form.get("engine_capacity_cc"), 50, 8000, 1500),
        "fuel_type": form.get("fuel_type", "Petrol"),
        "vehicle_age_years": clamp_int(form.get("vehicle_age_years"), 0, 60, 8),
        "vehicle_usage_type": form.get("vehicle_usage_type", "Private"),
        "registration_district": form.get("registration_district", "Colombo"),
        "parking_type": form.get("parking_type", "Garage"),
        "has_lpg_conversion": clamp_int(form.get("has_lpg_conversion"), 0, 1, 0),

        "customer_id": customer_id,
    }

    # ---------------- PREMIUM INPUTS ----------------
    base_premium = clamp_float(form.get("base_premium"), 0, 1e12, 0)
    other_discount = clamp_float(form.get("other_discount"), 0, 1e12, 0)

    if base_premium <= 0:
        errors["base_premium"] = "Base premium must be > 0."

    # If validation errors
    if errors:
        return render_template("register.html", errors=errors, result=None, premium=None, form=form)

    # ---------------- MODEL RISK ----------------
    try:
        result = calculate_risk(input_policy)
    except Exception as e:
        errors["model"] = f"Risk engine error: {str(e)}"
        return render_template("register.html", errors=errors, result=None, premium=None, form=form)

    risk_percent = float(result["risk_probability"]) * 100.0

    # ---------------- PREMIUM CALC ----------------
    premium = calculate_final_premium(
        base_premium=base_premium,
        risk_percent=risk_percent,
        ncb_percentage=input_policy["ncb_percentage"],
        other_discount=other_discount
    )

    # Display meta
    result_display = {
        **result,
        "customer": {"full_name": full_name, "nic": nic}
    }

    # overwrite exp in form (if clamped by age rule)
    form["years_of_driving_experience"] = str(years_of_driving_experience)

    return render_template("register.html", errors={}, result=result_display, premium=premium, form=form)

if __name__ == "__main__":
    app.run(debug=True)
