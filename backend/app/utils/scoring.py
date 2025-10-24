# scoring.py
from typing import List, Tuple
import pandas as pd

def calculate_readiness(revenue: float, profit: float, debt: float) -> Tuple[float, List[str]]:
    """
    Simple deterministic scoring function for demo purposes.
    Returns (score, insights)
    """
    if revenue <= 0:
        # avoid division by zero, penalize missing revenue
        score = 0.0
        insights = ["Revenue must be > 0 for a valid score"]
        return score, insights

    profit_ratio = profit / revenue
    debt_ratio = debt / revenue

    # Weighted formula: profitability positive, debt negative, baseline 50
    score_raw = (profit_ratio * 100 * 0.6) + ((1 - debt_ratio) * 100 * 0.3) + 10
    score = max(0.0, min(100.0, round(score_raw, 1)))

    insights = []
    if profit_ratio > 0.2:
        insights.append("Strong profitability (profit/revenue > 20%)")
    elif profit_ratio > 0.05:
        insights.append("Moderate profitability")
    else:
        insights.append("Low or no profitability — consider margin improvements")

    if debt_ratio > 1.0:
        insights.append("Debt exceeds annual revenue — high leverage risk")
    elif debt_ratio > 0.5:
        insights.append("High debt ratio — refinancing recommended")
    else:
        insights.append("Debt level appears manageable")

    if score > 75:
        insights.append("Good candidate for external funding")
    elif score > 50:
        insights.append("May be eligible for small loans with some conditions")
    else:
        insights.append("Not ready for lending — improve cashflow or reduce debt")

    return score, insights

def parse_csv_financials(file_stream) -> dict:
    """
    Expect a CSV with at least 'revenue','profit','debt' columns or monthly revenue rows.
    For demo, accept:
    - Single-row CSV: revenue, profit, debt
    - Multi-row monthly revenue: a 'revenue' column; sum it up as annual revenue
    """
    df = pd.read_csv(file_stream)
    # normalize column names
    cols = [c.strip().lower() for c in df.columns]
    df.columns = cols

    if {'revenue', 'profit', 'debt'}.issubset(set(cols)):
        # single-row or multi-row; take sum if multiple rows
        revenue = float(df['revenue'].sum())
        profit = float(df['profit'].sum())
        debt = float(df['debt'].sum())
    elif 'revenue' in cols:
        # assume monthly rows; annualize by summing
        revenue = float(df['revenue'].sum())
        profit = 0.0
        debt = 0.0
    else:
        raise ValueError("CSV must include 'revenue' or ('revenue','profit','debt') columns")

    return {"revenue": revenue, "profit": profit, "debt": debt}
