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
    other_discount: float = 0
) -> dict:
    """
    Final premium calculation using risk %
    """

    # 1️⃣ Risk loading
    loading_pct = get_risk_loading_percent(risk_percent)
    loading_amount = base_premium * loading_pct

    # 2️⃣ NCB discount
    ncb_discount = base_premium * (ncb_percentage / 100)

    # 3️⃣ Other discounts
    total_discount = ncb_discount + other_discount

    # 4️⃣ Final premium
    final_premium = base_premium + loading_amount - total_discount

    return {
        "base_premium": round(base_premium, 2),
        "risk_loading_percent": loading_pct * 100,
        "risk_loading_amount": round(loading_amount, 2),
        "ncb_discount": round(ncb_discount, 2),
        "other_discount": round(other_discount, 2),
        "final_premium": round(max(final_premium, 0), 2)
    }
