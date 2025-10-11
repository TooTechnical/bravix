"""
Bravix – Financial Indicators Module (Safe Version)
---------------------------------------------------
Handles missing or None data gracefully so the API never crashes.
"""

from typing import Dict, Any, Optional


# ---------- Utility ----------

def safe_num(x):
    """Return 0 if None, else the number itself."""
    return x if isinstance(x, (int, float)) else 0


def safe_div(a, b):
    """Safely divide two numbers."""
    a, b = safe_num(a), safe_num(b)
    return round(a / b, 4) if b != 0 else None


# ---------- Ratio Functions ----------

def current_liquidity_ratio(current_assets, current_liabilities):
    return safe_div(current_assets, current_liabilities)

def quick_ratio(current_assets, stocks, current_liabilities):
    return safe_div(safe_num(current_assets) - safe_num(stocks), current_liabilities)

def absolute_liquidity_ratio(cash, short_term_investments, short_term_liabilities):
    return safe_div(safe_num(cash) + safe_num(short_term_investments), short_term_liabilities)

def inventory_turnover(cost_of_sales, avg_inventory):
    return safe_div(cost_of_sales, avg_inventory)

def receivables_turnover(net_sales, avg_receivables):
    return safe_div(net_sales, avg_receivables)

def asset_turnover(revenue, avg_assets):
    return safe_div(revenue, avg_assets)

def dso(receivables_turnover_ratio):
    return safe_div(365, receivables_turnover_ratio)

def net_profit_margin(net_profit, revenue):
    val = safe_div(net_profit, revenue)
    return val * 100 if val is not None else None

def roa(net_profit, avg_assets):
    val = safe_div(net_profit, avg_assets)
    return val * 100 if val is not None else None

def roe(net_profit, avg_equity):
    val = safe_div(net_profit, avg_equity)
    return val * 100 if val is not None else None

def equity_ratio(equity, total_capital):
    val = safe_div(equity, total_capital)
    return val * 100 if val is not None else None

def dti(total_liabilities, total_income):
    val = safe_div(total_liabilities, total_income)
    return val * 100 if val is not None else None

def dscr_monthly(monthly_income, monthly_debt_payments):
    return safe_div(monthly_income, monthly_debt_payments)

def roi(profit_from_investment, investment_cost):
    val = safe_div(safe_num(profit_from_investment) - safe_num(investment_cost), investment_cost)
    return val * 100 if val is not None else None

def working_capital(current_assets, current_liabilities):
    return safe_num(current_assets) - safe_num(current_liabilities)

def efficiency_ratio(net_sales, working_capital_value):
    return safe_div(net_sales, working_capital_value)

def debt_to_ebitda(general_debt, ebitda):
    return safe_div(general_debt, ebitda)

def dscr_ebit(ebit, debt_service):
    return safe_div(ebit, debt_service)


# ---------- Status Evaluation ----------

def evaluate_status(indicator: str, value: Optional[float]) -> str:
    if value is None:
        return "insufficient data"

    ranges = {
        "Current Liquidity Ratio": (1.5, 2.0),
        "Quick Ratio": (1.0, 1.5),
        "Absolute Liquidity Ratio": (0.2, None),
        "Inventory Turnover": (5, 10),
        "Receivables Turnover": (5, 12),
        "Asset Turnover": (0.5, 2.0),
        "DSO": (None, 73),
        "Net Profit Margin (%)": (10, None),
        "ROA (%)": (5, None),
        "ROE (%)": (10, None),
        "Equity Ratio (%)": (40, None),
        "DTI (%)": (None, 35),
        "DSCR (Monthly)": (1.25, None),
        "ROI (%)": (5, None),
        "Working Capital": (0, None),
        "Efficiency Ratio": (1.0, None),
        "Debt-to-EBITDA": (None, 3.5),
        "DSCR (EBIT)": (1.25, None)
    }

    low, high = ranges.get(indicator, (None, None))

    if low is not None and high is not None:
        if low <= value <= high: return "good"
        elif (low * 0.8) <= value <= (high * 1.2): return "caution"
        else: return "poor"
    elif low is not None:
        if value >= low: return "good"
        elif value >= (low * 0.8): return "caution"
        else: return "poor"
    elif high is not None:
        if value <= high: return "good"
        elif value <= (high * 1.2): return "caution"
        else: return "poor"
    return "unknown"


# ---------- Combined Computation ----------

def compute_all(data: Dict[str, Any]):
    ratios = {
        "Current Liquidity Ratio": current_liquidity_ratio(data.get("current_assets"), data.get("current_liabilities")),
        "Quick Ratio": quick_ratio(data.get("current_assets"), data.get("stocks"), data.get("current_liabilities")),
        "Absolute Liquidity Ratio": absolute_liquidity_ratio(
            data.get("cash"), data.get("short_term_investments"), data.get("short_term_liabilities")),
        "Inventory Turnover": inventory_turnover(data.get("cost_of_sales"), data.get("avg_inventory")),
        "Receivables Turnover": receivables_turnover(data.get("net_sales"), data.get("avg_receivables")),
        "Asset Turnover": asset_turnover(data.get("revenue"), data.get("avg_assets")),
        "DSO": dso(receivables_turnover(data.get("net_sales"), data.get("avg_receivables"))),
        "Net Profit Margin (%)": net_profit_margin(data.get("net_profit"), data.get("revenue")),
        "ROA (%)": roa(data.get("net_profit"), data.get("avg_assets")),
        "ROE (%)": roe(data.get("net_profit"), data.get("avg_equity")),
        "Equity Ratio (%)": equity_ratio(data.get("equity"), data.get("total_capital")),
        "DTI (%)": dti(data.get("total_liabilities"), data.get("total_income")),
        "DSCR (Monthly)": dscr_monthly(data.get("monthly_income"), data.get("monthly_debt_payments")),
        "ROI (%)": roi(data.get("profit_from_investment"), data.get("investment_cost")),
        "Working Capital": working_capital(data.get("current_assets"), data.get("current_liabilities")),
        "Efficiency Ratio": efficiency_ratio(
            data.get("net_sales"), working_capital(data.get("current_assets"), data.get("current_liabilities"))),
        "Debt-to-EBITDA": debt_to_ebitda(data.get("general_debt"), data.get("ebitda")),
        "DSCR (EBIT)": dscr_ebit(data.get("ebit"), data.get("debt_service")),
    }

    result = []
    for name, value in ratios.items():
        result.append({
            "name": name,
            "value": value,
            "status": evaluate_status(name, value)
        })
    return {"ratios": result}
