"""
Braivix – AI Financial Analysis & Credit Evaluation
---------------------------------------------------
Performs dynamic quantitative scoring, stress testing, and narrative reasoning
to produce a full institutional-grade credit assessment report.
"""

import os, json
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
#  Helper: assign A–E grades from numeric indicator values
# ----------------------------------------------------------------------
def grade_indicator(name, value):
    """Assign grade and numeric score based on heuristic thresholds."""
    try:
        v = float(value)
    except Exception:
        return "C", 3  # default neutral

    name = name.lower()

    # Liquidity metrics
    if name in ["current_ratio", "quick_ratio", "cash_ratio"]:
        if v >= 2: return "A", 5
        if v >= 1.5: return "B", 4
        if v >= 1.0: return "C", 3
        if v >= 0.7: return "D", 2
        return "E", 1

    # Leverage
    if name in ["debt_to_equity_ratio", "debt_ratio"]:
        if v <= 0.3: return "A", 5
        if v <= 0.6: return "B", 4
        if v <= 1.0: return "C", 3
        if v <= 1.5: return "D", 2
        return "E", 1

    # Profitability
    if name in ["gross_profit_margin", "operating_profit_margin", "net_profit_margin"]:
        if v >= 20: return "A", 5
        if v >= 15: return "B", 4
        if v >= 10: return "C", 3
        if v >= 5: return "D", 2
        return "E", 1

    # Returns
    if name in ["return_on_assets", "return_on_equity", "return_on_investment"]:
        if v >= 15: return "A", 5
        if v >= 10: return "B", 4
        if v >= 5: return "C", 3
        if v >= 1: return "D", 2
        return "E", 1

    # Altman Z-Score
    if name == "altman_z_score":
        if v >= 3.0: return "A", 5
        if v >= 2.5: return "B", 4
        if v >= 1.8: return "C", 3
        if v >= 1.2: return "D", 2
        return "E", 1

    # Default fallback
    if v >= 5: return "A", 5
    if v >= 4: return "B", 4
    if v >= 3: return "C", 3
    if v >= 2: return "D", 2
    return "E", 1


# ----------------------------------------------------------------------
#  Weighted scoring logic
# ----------------------------------------------------------------------
def compute_weighted_score(indicator_scores: dict):
    weights = {
        "current_ratio": 0.08, "quick_ratio": 0.08, "cash_ratio": 0.08,
        "debt_to_equity_ratio": 0.10, "debt_ratio": 0.10, "interest_coverage_ratio": 0.10,
        "gross_profit_margin": 0.05, "operating_profit_margin": 0.05, "net_profit_margin": 0.05,
        "return_on_assets": 0.05, "return_on_equity": 0.05, "return_on_investment": 0.05,
        "asset_turnover_ratio": 0.05, "inventory_turnover": 0.05, "accounts_receivable_turnover": 0.05,
        "earnings_per_share": 0.025, "price_to_earnings_ratio": 0.025, "altman_z_score": 0.06
    }

    score = sum(weights[k] * indicator_scores.get(k, 3) for k in weights)
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
#  GPT-5 reasoning engine (main)
# ----------------------------------------------------------------------
def analyze_with_chatgpt(raw_text: str, indicators: dict, _, client: OpenAI = None):
    if client is None:
        client = get_openai_client()
    if not raw_text.strip():
        raw_text = "No extracted financial text available."

    # 1️⃣ Auto-grade each indicator
    graded_letters = {}
    graded_values = {}
    for name, val in indicators.items():
        letter, num = grade_indicator(name, val)
        graded_letters[name] = letter
        graded_values[name] = num

    # 2️⃣ Compute unique weighted score
    results = compute_weighted_score(graded_values)

    # 3️⃣ Debug log to confirm unique scores per file
    print(f"📊 Computed weighted_credit_score: {results['weighted_credit_score']}")
    print(f"📈 Evaluation_score: {results['evaluation_score']}")
    print(f"🧮 Graded indicators summary: {graded_letters}")

    # 4️⃣ Build GPT prompt
    prompt = f"""
You are a senior institutional credit analyst generating a **Detailed Credit Evaluation Report**.

--- INPUTS ---
Financial document excerpt (sanitized):
{raw_text[:2000]}

Parsed indicator values:
{json.dumps(indicators, indent=2)}

Auto-graded indicators (A–E → 5–1):
{json.dumps(graded_letters, indent=2)}

Weighted credit score calculation (Σ wᵢ×sᵢ):
{results['weighted_credit_score']} / 5  → Evaluation Score {results['evaluation_score']} / 100

--- TASK ---
Write a concise, data-driven institutional report with these sections:

1. Executive Summary  
2. Quantitative Breakdown Table  
3. Analyst Commentary (Why)  
4. Scenario Stress Test  
5. Benchmark Comparison  
6. Analyst Metrics Section  
7. Strategic Implications  
8. Final Evaluation Summary  

Be professional, objective, and clear – suitable for credit committee presentation.
"""

    # 5️⃣ GPT-5 + fallback to GPT-4o
    for model in ["gpt-5", "gpt-4o"]:
        try:
            completion = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are an institutional financial analyst."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.4,
                max_tokens=1800,
            )
            text = completion.choices[0].message.content.strip()
            if text:
                structured = {
                    "company_name": "Auto-detected or uploaded entity",
                    "analysis_timestamp": "auto",
                    "scores": results,
                    "summary": {
                        "executive_overview": "Automatically generated based on analyzed indicators.",
                        "primary_strengths": [
                            "Solid capital structure and consistent profitability metrics.",
                            "Reasonable solvency and coverage ratios."
                        ],
                        "primary_weaknesses": [
                            "Liquidity ratios may constrain flexibility.",
                            "Profit margins under moderate pressure."
                        ],
                    },
                    "final_evaluation": {
                        "weighted_credit_score": f"{results['weighted_credit_score']} / 5",
                        "evaluation_score": f"{results['evaluation_score']} / 100",
                        "risk_category": results["risk_category"],
                        "credit_decision": results["credit_decision"],
                    }
                }

                return {
                    "analysis_raw": text,
                    "scores": results,
                    "structured_report": structured,
                    "graded_indicators": graded_letters
                }
        except Exception as e:
            print(f"{model.upper()} failed: {e}")
            continue

    return {
        "analysis_raw": "No analysis generated.",
        "scores": results,
        "structured_report": {},
        "graded_indicators": graded_letters,
    }
