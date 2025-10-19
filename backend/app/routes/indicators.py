def calculate_indicators(data: dict):
    """
    Calculate 18 core financial indicators from parsed financial data.
    Handles missing values safely and returns a structured dictionary.
    """

    def safe_div(numerator, denominator):
        try:
            if denominator in (0, None): 
                return 0.0
            return round(float(numerator) / float(denominator), 4)
        except Exception:
            return 0.0

    # Extract key values with defaults
    revenue = float(data.get("revenue") or 0)
    profit = float(data.get("profit") or 0)
    debt = float(data.get("debt") or 0)
    assets = float(data.get("assets") or 0)
    equity = float(data.get("equity") or 0)
    current_assets = float(data.get("current_assets") or assets * 0.3)
    current_liabilities = float(data.get("current_liabilities") or debt * 0.4)
    inventory = float(data.get("inventory") or assets * 0.1)
    short_term_investments = float(data.get("short_term_investments") or 0)
    cash = float(data.get("cash") or 0)
    cost_of_sales = float(data.get("cost_of_sales") or revenue * 0.7)
    accounts_receivable = float(data.get("accounts_receivable") or revenue * 0.15)
    ebitda = float(data.get("ebitda") or profit * 1.2)
    investment_costs = float(data.get("investment_costs") or assets * 0.05)
    total_liabilities = float(data.get("total_liabilities") or debt)
    total_income = float(data.get("total_income") or revenue)
    monthly_debt_payments = float(data.get("monthly_debt_payments") or debt / 12)
    depreciation = float(data.get("depreciation") or ebitda * 0.15)

    # --- Indicator Calculations ---
    indicators = {}

    # 1. Current Ratio
    indicators["current_ratio"] = safe_div(current_assets, current_liabilities)

    # 2. Quick Ratio
    indicators["quick_ratio"] = safe_div(current_assets - inventory, current_liabilities)

    # 3. Absolute Liquidity Ratio
    indicators["absolute_liquidity_ratio"] = safe_div(cash + short_term_investments, current_liabilities)

    # 4. Inventory Turnover Ratio
    indicators["inventory_turnover_ratio"] = safe_div(cost_of_sales, inventory)

    # 5. Receivables Turnover Ratio
    indicators["receivables_turnover_ratio"] = safe_div(revenue, accounts_receivable)

    # 6. Asset Turnover
    indicators["asset_turnover"] = safe_div(revenue, assets)

    # 7. DSO (Days Sales Outstanding)
    receivables_turnover = indicators["receivables_turnover_ratio"]
    indicators["dso"] = round(safe_div(365, receivables_turnover), 2) if receivables_turnover > 0 else 0

    # 8. Net Profit Margin
    indicators["net_profit_margin"] = round(safe_div(profit, revenue) * 100, 2)

    # 9. Return on Assets (ROA)
    indicators["roa"] = round(safe_div(profit, assets) * 100, 2)

    # 10. Return on Equity (ROE)
    indicators["roe"] = round(safe_div(profit, equity) * 100, 2)

    # 11. Equity Ratio
    indicators["equity_ratio"] = round(safe_div(equity, (equity + debt)) * 100, 2)

    # 12. Debt-to-Income Ratio (DTI)
    indicators["dti"] = round(safe_div(total_liabilities, total_income) * 100, 2)

    # 13. Debt Service Coverage Ratio (DSCR)
    indicators["dscr"] = round(safe_div(total_income / 12, monthly_debt_payments), 2)

    # 14. Return on Investment (ROI)
    indicators["roi"] = round(safe_div((profit - investment_costs), investment_costs) * 100, 2)

    # 15. Working Capital
    indicators["working_capital"] = round(current_assets - current_liabilities, 2)

    # 16. Efficiency Ratio
    working_capital = indicators["working_capital"] or 1
    indicators["efficiency_ratio"] = round(safe_div(revenue, working_capital), 2)

    # 17. Debt-to-EBITDA
    indicators["debt_to_ebitda"] = round(safe_div(debt, ebitda), 2)

    # 18. DSCR (EBIT-based)
    ebit = profit + depreciation
    debt_service = monthly_debt_payments * 12
    indicators["dscr_ebit"] = round(safe_div(ebit, debt_service), 2)

    # --- Readiness Score ---
    score = (
        (indicators["current_ratio"] * 10)
        + (indicators["net_profit_margin"] / 2)
        + (indicators["roe"] / 2)
        + (100 - indicators["dti"]) / 5
    )
    indicators["readiness_score"] = min(round(score, 2), 100.0)

    return indicators
