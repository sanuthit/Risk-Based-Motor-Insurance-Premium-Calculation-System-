# premium_rules.py

def get_risk_loading_percent(risk_percent: float) -> float:
    """
    Company underwriting rules (editable)
    """
    if risk_percent < 15:
        return 0.00        # No loading
    elif risk_percent < 25:
        return 0.10        # +10%
    elif risk_percent < 40:
        return 0.25        # +25%
    else:
        return 0.50        # +50%


def calculate_final_premium(
    base_premium: float,
    risk_percent: float,
    ncb_percentage: float = 0,
    other_discount: float = 0,

    # --- Charges like your Excel (editable defaults) ---
    admin_fee_rate: float = 0.0291,   # 2.91%
    policy_fee: float = 200.0,        # LKR 200
    vat_rate: float = 0.18            # 18%
) -> dict:
    """
    Final premium calculation using risk %
    Returns a full breakdown including VAT/admin/policy fee.

    Structure (similar to your sheet):
    base_premium
    + risk_loading
    - discounts (NCB + other)
    = net_premium_before_fees
    + admin_fee
    + policy_fee
    = premium_before_vat
    + vat
    = total_payable
    """

    base_premium = float(base_premium)
    risk_percent = float(risk_percent)
    ncb_percentage = float(ncb_percentage)
    other_discount = float(other_discount)

    # 1) Risk loading
    loading_pct = get_risk_loading_percent(risk_percent)
    loading_amount = base_premium * loading_pct

    # 2) Discounts
    ncb_discount = base_premium * (ncb_percentage / 100.0)
    total_discount = ncb_discount + other_discount

    # 3) Net premium (before fees/taxes)
    net_premium = (base_premium + loading_amount) - total_discount
    net_premium = max(net_premium, 0.0)

    # 4) Admin fee + Policy fee
    admin_fee = net_premium * float(admin_fee_rate)
    premium_before_vat = net_premium + admin_fee + float(policy_fee)

    # 5) VAT
    vat_amount = premium_before_vat * float(vat_rate)

    # 6) Total payable
    total_payable = premium_before_vat + vat_amount

    return {
        "risk_percent": round(risk_percent, 2),

        "base_premium": round(base_premium, 2),

        "risk_loading_percent": round(loading_pct * 100, 2),
        "risk_loading_amount": round(loading_amount, 2),

        "ncb_percentage": round(ncb_percentage, 2),
        "ncb_discount": round(ncb_discount, 2),

        "other_discount": round(other_discount, 2),
        "total_discount": round(total_discount, 2),

        "net_premium_before_fees": round(net_premium, 2),

        "admin_fee_rate_percent": round(float(admin_fee_rate) * 100, 2),
        "admin_fee": round(admin_fee, 2),

        "policy_fee": round(float(policy_fee), 2),

        "premium_before_vat": round(premium_before_vat, 2),

        "vat_rate_percent": round(float(vat_rate) * 100, 2),
        "vat_amount": round(vat_amount, 2),

        "total_payable": round(total_payable, 2)
    }


# Optional quick test
if __name__ == "__main__":
    out = calculate_final_premium(
        base_premium=140825,
        risk_percent=54.36,
        ncb_percentage=70,
        other_discount=0
    )
    print(out)
