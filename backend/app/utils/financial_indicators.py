"""
Bravix – 18-Indicator Financial Health Engine (v4.0)
----------------------------------------------------
Computes liquidity, profitability, solvency, and efficiency metrics
with accurate formulas and rating logic aligned with Mariya’s model.
"""

from typing import Dict, Any, Optional


# ---------- Utility ----------

def safe_num(x):
    """Return 0 if None or invalid, else float(x)."""
    try:
        return float(x)
    except (TypeError, ValueError):
        return 0.0


def safe_div(a, b):
    """Safely divide two numbers."""
    a, b = safe_num(a), safe_num(b)
    return round(a / b, 4) if b not in (0, None, 0.0) else None


# ---------- Indicator Functions ----------

def current_ratio(assets, liabilities):
    return safe_div(assets, liabilities)

def quick_ratio(assets, inventory, liabilities):
    return safe_div(safe_num(assets) - safe_num(inventory), liabilities)

def cash_ratio(cash, liabilities):
    return safe_div(cash, liabilities)

def debt_to_equity(liabilities, equity):
    return safe_div(liabilities, equity)

def debt_ratio(liabilities, assets):
    return safe_div(liabilities, assets)

def interest_coverage(ebit, interest_expense):
    return safe_div(ebit, interest_expense)

def gross_profit_margin(gross_profit, revenue):
    val = safe_div(gross_profit, revenue)
    return round(val * 100, 2) if val is not None else None

def operating_profit_margin(ebit, revenue):
    val = safe_div(ebit, revenue)
    return round(val * 100, 2) if val is not None else None

def net_profit_margin(net_profit, revenue):
    val = safe_div(net_profit, revenue)
    return round(val * 100, 2) if val is not None else None

def return_on_assets(net_profit, assets):
    val = safe_div(net_profit, assets)
    return round(val * 100, 2) if val is not None else None

def return_on_equity(net_profit, equity):
    val = safe_div(net_profit, equity)
    return round(val * 100, 2) if val is not None else None

def return_on_investment(net_profit, investment):
    val = safe_div(net_profit, investment)
    return round(val * 100, 2) if val is not None else None

def asset_turnover(revenue, assets):
    return safe_div(revenue, assets)

def inventory_turnover(cost_of_sales, inventory):
    return safe_div(cost_of_sales, inventory)

def receivables_turnover(revenue, receivables):
    return safe_div(revenue, receivables)

def earnings_per_share(net_profit, shares):
    return safe_div(net_profit, shares)

def price_to_earnings(price_per_share, eps):
    return safe_div(price_per_share, eps)

def altman_z_score(assets, liabilities, equity, revenue, net_profit):
    # Simplified Z-Score proxy
    A = safe_div(assets - liabilities, assets)
    B = safe_div(retained_earnings := equity, assets)
    C = safe_div(ebit := net_profit * 1.15, assets)
    D = safe_div(revenue, assets)
    E = safe_div(equity, liabilities)
    return round(1.2*A + 1.4*B + 3.3*C + 0.6*D + 1.0*E, 2)


# ---------- Status Evaluation ----------

def evaluate_status(indicator: str, value: Optional[float]) -> str:
    """Classify each ratio into Good / Caution / Poor ranges."""
    if value is None:
        return "insufficient data"

    thresholds = {
        "current_ratio": (2, 1.5),
        "quick_ratio": (1, 0.8),
        "cash_ratio": (0.2, 0.1),
        "debt_to_equity_ratio": (0.5, 1.0),  # lower better
        "debt_ratio": (0.6, 0.8),
        "interest_coverage_ratio": (3, 1.5),
        "gross_profit_margin": (40, 20),
        "operating_profit_margin": (20, 10),
        "net_profit_margin": (10, 5),
        "return_on_assets": (8, 4),
        "return_on_equity": (15, 8),
        "return_on_investment": (10, 5),
        "asset_turnover_ratio": (1, 0.5),
        "inventory_turnover": (5, 2),
        "accounts_receivable_turnover": (7, 3),
        "earnings_per_share": (1, 0.5),
        "price_to_earnings_ratio": (20, 40),  # lower better
        "altman_z_score": (3, 1.8)
    }

    good, caution = thresholds.get(indicator, (None, None))

    if good is None:
        return "unknown"

    # Some ratios should be “lower is better”
    lower_better = indicator in ["debt_to_equity_ratio", "debt_ratio", "price_to_earnings_ratio"]

    if lower_better:
        if value <= good:
            return "good"
        elif value <= caution:
            return "caution"
        else:
            return "poor"
    else:
        if value >= good:
            return "good"
        elif value >= caution:
            return "caution"
        else:
            return "poor"


# ---------- Company Classification ----------

def classify_company(overall_score: float) -> Dict[str, Any]:
    """Assign class (A–E) based on score and map to standard ratings."""
    if overall_score is None:
        return {"company_class": "N/A", "risk": "N/A", "decision": "N/A", "ratings": {}}

    if overall_score >= 90:
        cls, risk, decision = "A", "Excellent", "Approve"
    elif overall_score >= 75:
        cls, risk, decision = "B", "Good", "Proceed"
    elif overall_score >= 60:
        cls, risk, decision = "C", "Average", "Caution"
    elif overall_score >= 40:
        cls, risk, decision = "D", "Weak", "Not Recommended"
    else:
        cls, risk, decision = "E", "Critical", "Decline"

    rating_map = {
        "A": {"Moodys": "Aaa–A2", "S&P": "AAA–A"},
        "B": {"Moodys": "Baa1–Baa3", "S&P": "BBB+"},
        "C": {"Moodys": "Ba1–Ba3", "S&P": "BB"},
        "D": {"Moodys": "B1–B3", "S&P": "B"},
        "E": {"Moodys": "Caa–C", "S&P": "CCC–D"},
    }

    return {
        "company_class": cls,
        "risk_category": risk,
        "credit_decision": decision,
        "ratings": rating_map.get(cls, {}),
    }


# ---------- Combined Computation ----------

def compute_all(data: Dict[str, Any]) -> Dict[str, Any]:
    """Compute all 18 indicators and classify company performance."""
    ratios = {
        "current_ratio": current_ratio(data.get("assets"), data.get("liabilities")),
        "quick_ratio": quick_ratio(data.get("assets"), data.get("inventory"), data.get("liabilities")),
        "cash_ratio": cash_ratio(data.get("cash"), data.get("liabilities")),
        "debt_to_equity_ratio": debt_to_equity(data.get("liabilities"), data.get("equity")),
        "debt_ratio": debt_ratio(data.get("liabilities"), data.get("assets")),
        "interest_coverage_ratio": interest_coverage(data.get("ebit"), data.get("interest_expense")),
        "gross_profit_margin": gross_profit_margin(data.get("gross_profit"), data.get("revenue")),
        "operating_profit_margin": operating_profit_margin(data.get("ebit"), data.get("revenue")),
        "net_profit_margin": net_profit_margin(data.get("profit"), data.get("revenue")),
        "return_on_assets": return_on_assets(data.get("profit"), data.get("assets")),
        "return_on_equity": return_on_equity(data.get("profit"), data.get("equity")),
        "return_on_investment": return_on_investment(data.get("profit"), data.get("investment")),
        "asset_turnover_ratio": asset_turnover(data.get("revenue"), data.get("assets")),
        "inventory_turnover": inventory_turnover(data.get("cost_of_sales"), data.get("inventory")),
        "accounts_receivable_turnover": receivables_turnover(data.get("revenue"), data.get("receivables")),
        "earnings_per_share": earnings_per_share(data.get("profit"), data.get("shares_outstanding")),
        "price_to_earnings_ratio": price_to_earnings(data.get("share_price"), earnings_per_share(data.get("profit"), data.get("shares_outstanding"))),
        "altman_z_score": altman_z_score(
            data.get("assets"), data.get("liabilities"), data.get("equity"),
            data.get("revenue"), data.get("profit")
        ),
    }

    results = []
    score_map = {"good": 1.0, "caution": 0.6, "poor": 0.2}
    total_score = 0
    valid_count = 0

    for k, v in ratios.items():
        status = evaluate_status(k, v)
        if status in score_map:
            total_score += score_map[status]
            valid_count += 1
        results.append({"name": k, "value": v, "status": status})

    overall_score = round((total_score / valid_count) * 100, 2) if valid_count else None
    classification = classify_company(overall_score)

    return {
        "indicators": results,
        "overall_health_score": overall_score,
        **classification
    }
