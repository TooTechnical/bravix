import os
from openai import OpenAI


def get_openai_client():
    """
    Safely creates an OpenAI client at runtime (Render-compatible).
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("Missing OPENAI_API_KEY environment variable")
    return OpenAI(api_key=api_key)

# ✅ Explicit base URL ensures connection works in all environments
    return OpenAI(
        api_key=api_key,
        base_url="https://api.openai.com/v1"
    )


def analyze_with_chatgpt(raw_text: str, indicators: dict, client: OpenAI = None):
    """
    Uses GPT-5 (preferred) or GPT-4o (fallback) to analyze financial risk
    using all 18 indicators. Produces a detailed, structured report.
    """

    # ✅ Ensure a valid client exists
    if client is None:
        client = get_openai_client()

    if not raw_text or raw_text.strip() == "":
        raw_text = "No extracted financial text available."

    # --- Build structured expert prompt ---
    prompt = f"""
You are a senior financial risk analyst. Evaluate this company’s financial health,
liquidity, profitability, leverage, solvency, and creditworthiness.

Base your analysis on the extracted document data and the following 18 key financial indicators.
For each indicator, compare the company's calculated value with the benchmark range and identify whether it is Healthy, Weak, or Concerning.

--- EXTRACTED DOCUMENT DATA ---
{raw_text[:2500]}

--- COMPUTED FINANCIAL INDICATORS (with expected healthy ranges) ---
1. Current Ratio = {indicators.get('current_ratio')} (Healthy: 1.5–2.0)
2. Quick Ratio = {indicators.get('quick_ratio')} (Healthy: 1.0–1.5)
3. Absolute Liquidity Ratio = {indicators.get('absolute_liquidity_ratio')} (≥ 0.2)
4. Inventory Turnover Ratio = {indicators.get('inventory_turnover_ratio')} (5–10)
5. Receivables Turnover Ratio = {indicators.get('receivables_turnover_ratio')} (5–12)
6. Asset Turnover = {indicators.get('asset_turnover')} (1–2)
7. DSO (Days Sales Outstanding) = {indicators.get('dso')} (≤ 30–45 days)
8. Net Profit Margin = {indicators.get('net_profit_margin')}% (≥ 10%)
9. Return on Assets (ROA) = {indicators.get('roa')}% (≥ 5–10%)
10. Return on Equity (ROE) = {indicators.get('roe')}% (≥ 15%)
11. Equity Ratio = {indicators.get('equity_ratio')}% (≥ 50%)
12. Debt-to-Income Ratio (DTI) = {indicators.get('dti')}% (≤ 30–40%)
13. Debt Service Coverage Ratio (DSCR) = {indicators.get('dscr')} (≥ 1.5)
14. Return on Investment (ROI) = {indicators.get('roi')}% (≥ 15%)
15. Working Capital = {indicators.get('working_capital')} (Positive)
16. Efficiency Ratio = {indicators.get('efficiency_ratio')} (≥ 1.5)
17. Debt-to-EBITDA = {indicators.get('debt_to_ebitda')} (≤ 3.5)
18. DSCR (EBIT-based) = {indicators.get('dscr_ebit')} (≥ 1.2)

--- READINESS SCORE ---
Overall Readiness Score = {indicators.get('readiness_score')}/100

Please analyze and respond using this structured format:

**Overview:**
Summarize the company’s overall financial condition and the reliability of the data.

**Indicator Comparison:**
Briefly comment on how each ratio compares to its healthy range.

**Strengths:**
Highlight areas where the company performs well.

**Weaknesses / Risk Factors:**
Identify concerning metrics or trends and explain why they increase financial risk.

**Liquidity Assessment:**
Is the company able to meet its short-term obligations?

**Profitability Assessment:**
Is the company generating sufficient returns from its operations?

**Solvency / Leverage Assessment:**
Evaluate the company’s long-term financial stability and debt exposure.

**Credit Decision Summary:**
Provide:
- Loan Recommendation (Approve / Review / Reject)
- Risk Level (Low / Medium / High)
- Risk Score (0–100)
- Final Summary (1–2 paragraphs explaining the overall judgment)
"""

    # ✅ Attempt GPT-5 first, fallback to GPT-4o
    for model in ["gpt-5", "gpt-4o"]:
        try:
            print(f"\n🧠 Sending this summary to {model.upper()}...\n{'-'*60}")

            completion = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are an expert financial and credit risk analyst."},
                    {"role": "user", "content": prompt},
                ],
                **(
                    {"max_completion_tokens": 1000}
                    if model == "gpt-5"
                    else {"max_tokens": 1000}
                ),
            )

            text = completion.choices[0].message.content.strip()
            if text:
                print(f"✅ AI analysis complete using {model}")
                return {"analysis_raw": text}

        except Exception as e:
            print(f"⚠️ {model} failed:", e)
            continue

    # ❌ If both fail
    print("❌ No models succeeded.")
    return {"analysis_raw": "No analysis returned by GPT-5 or GPT-4o."}
