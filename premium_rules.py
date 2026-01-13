def calculate_base_premium(
    sum_insured_lkr: float,
    vehicle_type: str,
    vehicle_usage_type: str
) -> float:

    sum_insured_lkr = float(sum_insured_lkr)
    vt = vehicle_type.lower()
    usage = vehicle_usage_type.lower()

    # Tariff rates
    if vt == "car":
        rate = 0.025
    elif vt in ["suv", "van"]:
        rate = 0.028
    elif vt in ["truck", "bus"]:
        rate = 0.035
    elif vt == "motorcycle":
        rate = 0.035
    elif vt in ["three-wheeler", "three wheeler"]:
        rate = 0.038
    else:
        rate = 0.03

    # Commercial / hire loading
    if usage in ["business", "rent", "taxi", "hire", "commercial", "school"]:
        rate *= 1.35

    base_premium = sum_insured_lkr * rate

    # Minimum premium
    return round(max(base_premium, 15000.0), 2)


# --------------------------------------------------
# RISK LOADING RULES
# --------------------------------------------------
def get_risk_loading_percent(risk_percent: float) -> float:
    if risk_percent < 15:
        return 0.00
    elif risk_percent < 25:
        return 0.10
    elif risk_percent < 40:
        return 0.25
    else:
        return 0.50


# --------------------------------------------------
# FINAL PREMIUM CALCULATION
# --------------------------------------------------
def calculate_final_premium(
    base_premium: float,
    risk_percent: float,
    ncb_percentage: float = 0,
    other_discount: float = 0,
    admin_fee_rate: float = 0.0291,
    policy_fee: float = 200.0,
    vat_rate: float = 0.18
) -> dict:

    base_premium = float(base_premium)

    # Risk loading
    loading_pct = get_risk_loading_percent(risk_percent)
    loading_amount = base_premium * loading_pct

    # Discounts
    ncb_discount = base_premium * (ncb_percentage / 100)
    total_discount = ncb_discount + other_discount

    # Net premium
    net_premium = max((base_premium + loading_amount) - total_discount, 0)

    # Fees
    admin_fee = net_premium * admin_fee_rate
    premium_before_vat = net_premium + admin_fee + policy_fee

    # VAT
    vat_amount = premium_before_vat * vat_rate
    total_payable = premium_before_vat + vat_amount

    return {
        "base_premium": round(base_premium, 2),
        "risk_percent": round(risk_percent, 2),
        "risk_loading_percent": round(loading_pct * 100, 2),
        "risk_loading_amount": round(loading_amount, 2),
        "ncb_percentage": round(ncb_percentage, 2),
        "ncb_discount": round(ncb_discount, 2),
        "net_premium": round(net_premium, 2),
        "admin_fee": round(admin_fee, 2),
        "policy_fee": round(policy_fee, 2),
        "vat_amount": round(vat_amount, 2),
        "total_payable": round(total_payable, 2),
    }


# --------------------------------------------------
# QUICK TEST
# --------------------------------------------------
if __name__ == "__main__":

    base = calculate_base_premium(
        sum_insured_lkr=3000000,
        vehicle_type="Car",
        vehicle_usage_type="Private"
    )

    result = calculate_final_premium(
        base_premium=base,
        risk_percent=32.5,
        ncb_percentage=20
    )

    print("Base Premium:", base)
    print(result)
