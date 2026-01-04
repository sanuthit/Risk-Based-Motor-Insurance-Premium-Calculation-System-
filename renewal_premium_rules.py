# premium_rules.py

def get_rebate_rate(sum_insured: float) -> float:
    """
    Private car rebate schedule (example – adjustable to company rules)
    """
    if 3_100_000 <= sum_insured <= 4_999_999:
        return 0.10
    elif 5_000_000 <= sum_insured <= 6_999_999:
        return 0.125
    elif 7_000_000 <= sum_insured <= 7_999_999:
        return 0.15
    elif sum_insured >= 8_000_000:
        return 0.20
    return 0.0


def calculate_base_premium(sum_insured: float, base_rate: float = 0.028):
    """
    Base premium from sum insured
    """
    return sum_insured * base_rate


def risk_loading(expected_claim: float) -> float:
    """
    Converts expected claim amount into loading %
    """
    if expected_claim < 50_000:
        return 0.00
    elif expected_claim < 200_000:
        return 0.05
    elif expected_claim < 500_000:
        return 0.10
    elif expected_claim < 1_000_000:
        return 0.20
    else:
        return 0.30


def calculate_final_premium(
    sum_insured: float,
    expected_claim: float,
    ncb_rate: float = 0.0
) -> dict:
    """
    Master premium calculator
    """

    base_premium = calculate_base_premium(sum_insured)

    rebate = base_premium * get_rebate_rate(sum_insured)
    loading = base_premium * risk_loading(expected_claim)
    ncb_discount = base_premium * ncb_rate

    net_premium = base_premium - rebate - ncb_discount + loading

    admin_fee = net_premium * 0.0291
    policy_fee = 200.0
    vat = 0.18 * (net_premium + admin_fee + policy_fee)

    total_premium = net_premium + admin_fee + policy_fee + vat

    return {
        "base_premium": round(base_premium, 2),
        "rebate": round(rebate, 2),
        "risk_loading": round(loading, 2),
        "ncb_discount": round(ncb_discount, 2),
        "admin_fee": round(admin_fee, 2),
        "policy_fee": policy_fee,
        "vat": round(vat, 2),
        "total_premium": round(total_premium, 2),
    }
