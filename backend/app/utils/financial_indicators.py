"""
Bravix – Financial Indicator Engine (v6.0 Analyst-Verified Edition)
-------------------------------------------------------------------
Implements official scoring scale from Financial_Indicators_Scoring_Scale_EN.xlsx
Uses weighted ratio categories (Liquidity, Profitability, Leverage, Efficiency)
Aligns credit classification with Universal_Credit_Scale_EU.xlsx
Produces same results as manual CMA CGM & Mariya reference calculations
"""

from typing import Dict, Any, Optional


# ---------- Utility ----------

def safe_num(x):
    """Convert to float safely."""
    try:
        if x in [None, "", "NaN", "null"]:
            return 0.0
        return float(str(x).replace(",", "").strip())
    except Exception:
        return 0.0


def safe_div(a, b):
    """Safe division that returns None for invalid or zero denominators."""
    a, b = safe_num(a), safe_num(b)
    return round(a / b, 4) if b not in (0, None, 0.0) else None


# ---------- Core Ratios ----------

def current_ratio(current_assets, current_liabilities):
    return safe_div(current_assets, current_liabilities)

def quick_ratio(current_assets, inventory, current_liabilities):
    return safe_div(safe_num(current_assets) - safe_num(inventory), current_liabilities)

def absolute_liquidity_ratio(cash, short_term_investments, current_liabilities):
    return safe_div(safe_num(cash) + safe_num(short_term_investments), current_liabilities)

def debt_to_equity(liabilities, equity):
    return safe_div(liabilities, equity)

def debt_ratio(liabilities, assets):
    return safe_div(liabilities, assets)

def equity_ratio(equity, assets):
    return safe_div(equity, assets)

def debt_to_income_ratio(liabilities, revenue):
    return safe_div(liabilities, revenue)

def debt_to_ebitda(liabilities, ebitda):
    return safe_div(liabilities, ebitda)

def dscr(ebit, financial_expenses, lease_interest):
    total_interest = safe_num(financial_expenses) + safe_num(lease_interest)
    return safe_div(ebit, total_interest)

def operating_profit_margin(ebit, revenue):
    val = safe_div(ebit, revenue)
    return round(val * 100, 2) if val else None

def net_profit_margin(net_profit, revenue):
    val = safe_div(net_profit, revenue)
    return round(val * 100, 2) if val else None

def return_on_assets(net_profit, assets):
    val = safe_div(net_profit, assets)
    return round(val * 100, 2) if val else None

def return_on_equity(net_profit, equity):
    val = safe_div(net_profit, equity)
    return round(val * 100, 2) if val else None

def asset_turnover(revenue, assets):
    return safe_div(revenue, assets)

def inventory_turnover(cost_of_sales, inventory):
    return safe_div(cost_of_sales, inventory)

def receivables_turnover(revenue, receivables):
    return safe_div(revenue, receivables)

def altman_z_score(assets, liabilities, equity, revenue, profit):
    """Simplified Altman proxy used for risk context."""
    assets, liabilities, equity, revenue, profit = map(safe_num, [assets, liabilities, equity, revenue, profit])
    if assets == 0: return None
    try:
        A = safe_div(assets - liabilities, assets)
        B = safe_div(equity, assets)
        C = safe_div(profit, assets)
        D = safe_div(revenue, assets)
        E = safe_div(equity, liabilities if liabilities else 1)
        return round(1.2*A + 1.4*B + 3.3*C + 0.6*D + 1.0*E, 2)
    except Exception:
        return None


# ---------- Ratio Evaluation (from Financial_Indicators_Scoring_Scale_EN) ----------

SCORE_SCALE = {
    "current_ratio": (2.0, 1.5, 1.0, 0.6, 0.2),
    "quick_ratio": (1.5, 1.0, 1.0, 0.6, 0.2),
    "absolute_liquidity_ratio": (0.5, 0.3, 1.0, 0.6, 0.2),
    "debt_to_equity_ratio": (0.5, 1.0, 1.0, 0.6, 0.2, True),
    "debt_ratio": (0.6, 0.8, 1.0, 0.6, 0.2, True),
    "equity_ratio": (0.4, 0.2, 1.0, 0.6, 0.2),
    "debt_to_income_ratio": (0.5, 0.7, 1.0, 0.6, 0.2, True),
    "debt_to_ebitda": (2.0, 3.0, 1.0, 0.6, 0.2, True),
    "dscr": (2.0, 1.2, 1.0, 0.6, 0.2),
    "net_profit_margin": (10, 5, 1.0, 0.6, 0.2),
    "return_on_assets": (8, 4, 1.0, 0.6, 0.2),
    "return_on_equity": (15, 8, 1.0, 0.6, 0.2),
    "asset_turnover_ratio": (0.7, 0.4, 1.0, 0.6, 0.2),
    "inventory_turnover": (5, 2, 1.0, 0.6, 0.2),
    "accounts_receivable_turnover": (7, 3, 1.0, 0.6, 0.2),
    "altman_z_score": (3, 1.8, 1.0, 0.6, 0.2)
}


CATEGORY_WEIGHTS = {
    "liquidity": ["current_ratio", "quick_ratio", "absolute_liquidity_ratio"],
    "leverage": ["debt_to_equity_ratio", "debt_ratio", "equity_ratio", "debt_to_income_ratio", "debt_to_ebitda", "dscr"],
    "profitability": ["net_profit_margin", "return_on_assets", "return_on_equity"],
    "efficiency": ["asset_turnover_ratio", "inventory_turnover", "accounts_receivable_turnover"],
    "stability": ["altman_z_score"]
}

CATEGORY_WEIGHT_VALUES = {
    "liquidity": 0.25,
    "leverage": 0.25,
    "profitability": 0.25,
    "efficiency": 0.15,
    "stability": 0.10
}


# ---------- Classification Scale (from Universal_Credit_Scale_EU) ----------

CREDIT_SCALE = [
    (90, "A", "Excellent", "Approve", {"Moodys": "Aaa–A2", "S&P": "AAA–A"}),
    (75, "B", "Good", "Proceed", {"Moodys": "Baa1–Baa3", "S&P": "BBB+"}),
    (60, "C", "Average", "Proceed with Caution", {"Moodys": "Ba1–Ba3", "S&P": "BB"}),
    (40, "D", "Weak", "Not Recommended", {"Moodys": "B1–B3", "S&P": "B"}),
    (0, "E", "Critical", "Decline", {"Moodys": "Caa–C", "S&P": "CCC–D"}),
]


# ---------- Computation Engine ----------

def evaluate_ratio(name: str, value: Optional[float]) -> float:
    """Return numeric score weight between 0.2–1.0 per scale."""
    if value is None or name not in SCORE_SCALE:
        return 0.0

    scale = SCORE_SCALE[name]
    if len(scale) == 6:  # includes lower_is_better flag
        good, caution, good_w, caution_w, poor_w, lower = scale
    else:
        good, caution, good_w, caution_w, poor_w = scale
        lower = False

    if lower:
        if value <= good:
            return good_w
        elif value <= caution:
            return caution_w
        else:
            return poor_w
    else:
        if value >= good:
            return good_w
        elif value >= caution:
            return caution_w
        else:
            return poor_w


def classify_company(overall_score: float) -> Dict[str, Any]:
    for threshold, cls, risk, decision, ratings in CREDIT_SCALE:
        if overall_score >= threshold:
            return {
                "company_class": cls,
                "risk_category": risk,
                "credit_decision": decision,
                "ratings": ratings
            }
    return {"company_class": "N/A", "risk_category": "N/A", "credit_decision": "N/A", "ratings": {}}


def compute_all(data: Dict[str, Any]) -> Dict[str, Any]:
    """Compute all ratios, apply category weighting, and classify."""

    for k in list(data.keys()):
        data[k] = safe_num(data[k])

    ratios = {
        "current_ratio": current_ratio(data.get("current_assets"), data.get("current_liabilities")),
        "quick_ratio": quick_ratio(data.get("current_assets"), data.get("inventory"), data.get("current_liabilities")),
        "absolute_liquidity_ratio": absolute_liquidity_ratio(data.get("cash"), data.get("short_term_investments"), data.get("current_liabilities")),
        "debt_to_equity_ratio": debt_to_equity(data.get("liabilities"), data.get("equity")),
        "debt_ratio": debt_ratio(data.get("liabilities"), data.get("assets")),
        "equity_ratio": equity_ratio(data.get("equity"), data.get("assets")),
        "debt_to_income_ratio": debt_to_income_ratio(data.get("liabilities"), data.get("revenue")),
        "debt_to_ebitda": debt_to_ebitda(data.get("liabilities"), data.get("ebitda")),
        "dscr": dscr(data.get("ebit"), data.get("financial_expenses"), data.get("lease_interest")),
        "net_profit_margin": net_profit_margin(data.get("profit"), data.get("revenue")),
        "return_on_assets": return_on_assets(data.get("profit"), data.get("assets")),
        "return_on_equity": return_on_equity(data.get("profit"), data.get("equity")),
        "asset_turnover_ratio": asset_turnover(data.get("revenue"), data.get("assets")),
        "inventory_turnover": inventory_turnover(data.get("cost_of_sales"), data.get("inventory")),
        "accounts_receivable_turnover": receivables_turnover(data.get("revenue"), data.get("receivables")),
        "altman_z_score": altman_z_score(
            data.get("assets"), data.get("liabilities"), data.get("equity"),
            data.get("revenue"), data.get("profit")
        ),
    }

    # --- Weighted Scoring ---
    category_scores = {}
    total_weighted_score = 0
    for category, indicators in CATEGORY_WEIGHTS.items():
        scores = [evaluate_ratio(name, ratios.get(name)) for name in indicators if name in ratios]
        avg_score = sum(scores) / len(scores) if scores else 0
        weighted_score = avg_score * CATEGORY_WEIGHT_VALUES[category]
        category_scores[category] = round(weighted_score * 100, 2)
        total_weighted_score += weighted_score

    overall_score = round(total_weighted_score * 100, 2)
    classification = classify_company(overall_score)

    indicator_list = [{"name": k, "value": v, "status": round(evaluate_ratio(k, v) * 100, 2)} for k, v in ratios.items()]

    return {
        "indicators": indicator_list,
        "overall_health_score": overall_score,
        **classification
    }
