"""
Braivix – AI Financial Analysis & Credit Evaluation
---------------------------------------------------
Performs quantitative scoring, stress testing, and narrative reasoning
to produce a full institutional-grade credit assessment report.
"""

import os, json, math
from openai import OpenAI

# ----------------------------------------------------------------------
#  OpenAI client setup
# ----------------------------------------------------------------------
def get_openai_client():
    api_key = os.getenv("OPENAI_API_KEY")
    base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    if not api_key:
        raise ValueError("Missing OPENAI_API_KEY.")
    return OpenAI(api_key=api_key, base_url=base_url)

# ----------------------------------------------------------------------
#  Core financial evaluation logic
# ----------------------------------------------------------------------
def compute_weighted_score(grades: dict):
    """Σ(wᵢ×sᵢ) weighted credit score and derived metrics."""
    weights = {
        "current_ratio": 0.08, "quick_ratio": 0.08, "cash_ratio": 0.08,
        "debt_to_equity_ratio": 0.10, "debt_ratio": 0.10, "interest_coverage_ratio": 0.10,
        "gross_profit_margin": 0.05, "operating_profit_margin": 0.05, "net_profit_margin": 0.05,
        "return_on_assets": 0.05, "return_on_equity": 0.05, "return_on_investment": 0.05,
        "asset_turnover_ratio": 0.05, "inventory_turnover": 0.05, "accounts_receivable_turnover": 0.05,
        "earnings_per_share": 0.025, "price_to_earnings_ratio": 0.025, "altman_z_score": 0.06
    }

    score = sum(weights[k] * grades.get(k, 3) for k in weights)
    evaluation_score = round((score / 5) * 100, 1)

    if evaluation_score >= 90:
        category, decision = "Excellent", "Safe to Proceed"
    elif evaluation_score >= 76:
        category, decision = "Good", "Safe to Proceed"
    elif evaluation_score >= 60:
        category, decision = "Average", "Proceed with Caution"
    elif evaluation_score >= 40:
        category, decision = "Weak", "Not Recommended"
    else:
        category, decision = "Critical", "Decline"

    return {
        "weighted_credit_score": round(score, 2),
        "evaluation_score": evaluation_score,
        "risk_category": category,
        "credit_decision": decision
    }

# ----------------------------------------------------------------------
#  GPT-5 reasoning engine
# ----------------------------------------------------------------------
def analyze_with_chatgpt(raw_text: str, indicators: dict, grades: dict, client: OpenAI = None):
    if client is None:
        client = get_openai_client()
    if not raw_text.strip():
        raw_text = "No extracted financial text available."

    results = compute_weighted_score(grades)

    # ---------- prompt ----------
    prompt = f"""
You are a senior credit-risk analyst generating a **Detailed Credit Evaluation Report**.

--- INPUTS ---
Financial document excerpt (sanitized):
{raw_text[:2000]}

Computed indicator values:
{json.dumps(indicators, indent=2)}

Indicator grades (A–E → 5–1):
{json.dumps(grades, indent=2)}

Weighted score computation (Σ wᵢ×sᵢ):
{results['weighted_credit_score']} / 5  → Evaluation Score {results['evaluation_score']} / 100

--- TASK ---
Write a professional, data-driven report with these sections:

1. **Executive Summary** – Concise overview showing numeric score, evaluation (0–100),
   credit decision, and one-sentence rationale.

2. **Quantitative Breakdown Table**
   - Liquidity, Leverage, Profitability, Efficiency, Solvency, Market.
   - Include category averages, weight contribution %, and comments.

3. **Analyst Commentary (Why)**
   Explain key positive and negative drivers behind each major category.

4. **Scenario Stress Test**
   Model a case where revenue ↓10% and interest expense ↑15%.
   Estimate the new weighted score and evaluation score impact (in % terms).

5. **Benchmark Comparison**
   Compare each key ratio to typical industry medians (infer where not supplied).
   Discuss whether the company performs above or below peers.

6. **Analyst Metrics Section**
   Report the following advanced indicators (approximate where necessary):
   - Liquidity Coverage Index
   - Leverage Multiple (Debt / EBITDA)
   - Profitability Spread (ROE – ROA)
   - Solvency Cushion (Equity / Total Assets)
   - Altman Z-Score Projection
   Each with interpretation in one sentence.

7. **Strategic Implications**
   Outline 3–5 management actions that could raise the company’s
   evaluation category within 12 months.

8. **Final Evaluation Summary**
   Weighted Credit Score: {results['weighted_credit_score']} / 5
   Evaluation Score: {results['evaluation_score']} / 100
   Risk Category: {results['risk_category']}
   Credit Decision: {results['credit_decision']}

The tone must be formal, concise, and suitable for presentation to
a credit committee or institutional investor. Avoid marketing language.
"""

    # ---------- model call ----------
    for model in ["gpt-5", "gpt-4o"]:
        try:
            completion = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are an institutional credit-risk analyst."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.4,
                max_tokens=1800,
            )
            text = completion.choices[0].message.content.strip()
            if text:
                return {
                    "analysis_raw": text,
                    "scores": results,
                }
        except Exception as e:
            print(f"{model.upper()} failed: {e}")
            continue

    return {"analysis_raw": "No analysis generated.", "scores": results}
