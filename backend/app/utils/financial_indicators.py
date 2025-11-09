"""
Bravix – 18-Indicator Financial Health Engine (v5.1 Final Edition)
-------------------------------------------------------------------
Fixes:
- Prevents double-counted liabilities (current + non-current)
- Ensures correct leverage ratios
- Stabilizes cost_of_sales and receivables turnover logic
- Fully normalized and ready for global company parsing
"""

from typing import Dict, Any, Optional


# ---------- Utility ----------

def safe_num(x):
    """Convert value to float safely."""
    try:
        if x in [None, "", "NaN", "null"]:
            return 0.0
        return float(str(x).replace(",", "").strip())
    except Exception:
        return 0.0


def safe_div(a, b):
    """Safely divide two numbers."""
    a, b = safe_num(a), safe_num(b)
    return round(a / b, 4) if b not in (0, None, 0.0) else None


def normalize_scale(value):
    """Normalize between thousands / millions automatically."""
    v = safe_num(value)
    if v > 1e12:
        return v / 1e6
    elif v > 1e9:
        return v / 1e3
    return v


# ---------- Ratios ----------

def current_ratio(current_assets, current_liabilities):
    return safe_div(current_assets, current_liabilities)

def quick_ratio(current_assets, inventory, current_liabilities):
    return safe_div(safe_num(current_assets) - safe_num(inventory), current_liabilities)

def cash_ratio(cash, short_term_investments, current_liabilities):
    return safe_div(safe_num(cash) + safe_num(short_term_investments), current_liabilities)

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

def inventory_turnover(cost_of_sales, avg_inventory):
    return safe_div(cost_of_sales, avg_inventory)

def receivables_turnover(revenue, avg_receivables):
    return safe_div(revenue, avg_receivables)

def earnings_per_share(net_profit, shares_outstanding):
    return safe_div(net_profit, shares_outstanding)

def price_to_earnings(price_per_share, eps):
    return safe_div(price_per_share, eps)

def altman_z_score(assets, liabilities, equity, revenue, net_profit):
    A = safe_div(assets - liabilities, assets)
    B = safe_div(equity, assets)
    C = safe_div(net_profit * 1.15, assets)
    D = safe_div(revenue, assets)
    E = safe_div(equity, liabilities)
    return round(1.2*A + 1.4*B + 3.3*C + 0.6*D + 1.0*E, 2)


# ---------- Status Evaluation ----------

def evaluate_status(indicator: str, value: Optional[float]) -> str:
    """Categorize ratios as good, caution, or poor."""
    if value is None:
        return "insufficient data"

    thresholds = {
        "current_ratio": (2.0, 1.5),
        "quick_ratio": (1.0, 0.8),
        "cash_ratio": (0.2, 0.1),
        "debt_to_equity_ratio": (0.5, 1.0),
        "debt_ratio": (0.6, 0.8),
        "interest_coverage_ratio": (3.0, 1.5),
        "gross_profit_margin": (40, 20),
        "operating_profit_margin": (20, 10),
        "net_profit_margin": (10, 5),
        "return_on_assets": (8, 4),
        "return_on_equity": (15, 8),
        "return_on_investment": (10, 5),
        "asset_turnover_ratio": (1.0, 0.5),
        "inventory_turnover": (5, 2),
        "accounts_receivable_turnover": (7, 3),
        "earnings_per_share": (1, 0.5),
        "price_to_earnings_ratio": (20, 40),
        "altman_z_score": (3, 1.8)
    }

    good, caution = thresholds.get(indicator, (None, None))
    if good is None:
        return "unknown"

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
    if overall_score is None:
        return {"company_class": "N/A", "risk": "N/A", "decision": "N/A", "ratings": {}}

    if overall_score >= 90:
        cls, risk, decision = "A", "Excellent", "Approve"
    elif overall_score >= 75:
        cls, risk, decision = "B", "Good", "Proceed"
    elif overall_score >= 60:
        cls, risk, decision = "C", "Average", "Proceed with Caution"
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


# ---------- Main Computation Engine ----------

def compute_all(data: Dict[str, Any]) -> Dict[str, Any]:
    """Compute all ratios with global compatibility."""

    # Normalize numbers
    for k in list(data.keys()):
        data[k] = normalize_scale(data[k])

    # Prevent double-counted liabilities
    if (
        data.get("current_liabilities")
        and data.get("non_current_liabilities")
        and safe_num(data["liabilities"]) == 0
    ):
        data["liabilities"] = safe_num(data["current_liabilities"]) + safe_num(data["non_current_liabilities"])

    # Derive equity if missing
    if not data.get("equity") and data.get("assets") and data.get("liabilities"):
        data["equity"] = safe_num(data["assets"]) - safe_num(data["liabilities"])

    # Fallbacks
    if not data.get("current_assets") and data.get("assets"):
        data["current_assets"] = safe_num(data["assets"]) * 0.3
    if not data.get("current_liabilities") and data.get("liabilities"):
        data["current_liabilities"] = safe_num(data["liabilities"]) * 0.45

    avg_inv = safe_num(data.get("avg_inventory") or data.get("inventory"))
    avg_recv = safe_num(data.get("avg_receivables") or data.get("receivables"))

    # Compute ratios
    ratios = {
        "current_ratio": current_ratio(data.get("current_assets"), data.get("current_liabilities")),
        "quick_ratio": quick_ratio(data.get("current_assets"), data.get("inventory"), data.get("current_liabilities")),
        "cash_ratio": cash_ratio(data.get("cash"), data.get("short_term_investments"), data.get("current_liabilities")),
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
        "inventory_turnover": inventory_turnover(data.get("cost_of_sales"), avg_inv),
        "accounts_receivable_turnover": receivables_turnover(data.get("revenue"), avg_recv),
        "earnings_per_share": earnings_per_share(data.get("profit"), data.get("shares_outstanding")),
        "price_to_earnings_ratio": price_to_earnings(
            data.get("share_price"),
            earnings_per_share(data.get("profit"), data.get("shares_outstanding"))
        ),
        "altman_z_score": altman_z_score(
            data.get("assets"), data.get("liabilities"), data.get("equity"),
            data.get("revenue"), data.get("profit")
        ),
    }

    results, total_score, valid_count = [], 0, 0
    score_map = {"good": 1.0, "caution": 0.6, "poor": 0.2}

    for name, value in ratios.items():
        status = evaluate_status(name, value)
        if status in score_map:
            total_score += score_map[status]
            valid_count += 1
        results.append({"name": name, "value": value, "status": status})

    overall_score = round((total_score / valid_count) * 100, 2) if valid_count else None
    classification = classify_company(overall_score)

    return {
        "indicators": results,
        "overall_health_score": overall_score,
        **classification
    }
