"""
Braivix – Dynamic Multilingual AI Financial Analysis & Credit Evaluation
------------------------------------------------------------------------
Computes indicator grades, weighted scores, and generates GPT-5/4o-based
narrative credit evaluation reports in any language, always outputting
English reports for consistency.
"""

import os
import json
from openai import OpenAI


# ----------------------------------------------------------------------
#  GPT client setup
# ----------------------------------------------------------------------
def get_openai_client():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("Missing OPENAI_API_KEY environment variable")
    return OpenAI(api_key=api_key)


# ----------------------------------------------------------------------
#  Grade mapping helper
# ----------------------------------------------------------------------
def grade_indicator(value, good_high=True):
    """Assign grade (A–E → 5–1) based on financial direction."""
    try:
        v = float(value)
        if good_high:
            if v >= 2:
                return 5
            elif v >= 1.5:
                return 4
            elif v >= 1.0:
                return 3
            elif v >= 0.5:
                return 2
            else:
                return 1
        else:  # smaller is better (e.g., debt ratios)
            if v <= 0.3:
                return 5
            elif v <= 0.5:
                return 4
            elif v <= 0.7:
                return 3
            elif v <= 1.0:
                return 2
            else:
                return 1
    except Exception:
        return 3  # neutral fallback


# ----------------------------------------------------------------------
#  Weighted score computation
# ----------------------------------------------------------------------
def compute_weighted_score(indicators: dict):
    """Derive grades dynamically from indicators and compute Σ(wᵢ×sᵢ)."""
    weights = {
        "current_ratio": 0.08,
        "quick_ratio": 0.08,
        "cash_ratio": 0.08,
        "debt_to_equity_ratio": 0.10,
        "debt_ratio": 0.10,
        "interest_coverage_ratio": 0.10,
        "gross_profit_margin": 0.05,
        "operating_profit_margin": 0.05,
        "net_profit_margin": 0.05,
        "return_on_assets": 0.05,
        "return_on_equity": 0.05,
        "return_on_investment": 0.05,
        "asset_turnover_ratio": 0.05,
        "inventory_turnover": 0.05,
        "accounts_receivable_turnover": 0.05,
        "earnings_per_share": 0.025,
        "price_to_earnings_ratio": 0.025,
        "altman_z_score": 0.06,
    }

    grades = {}
    for k in weights:
        if "debt" in k or "ratio" in k:
            grades[k] = grade_indicator(indicators.get(k, 0), good_high=False)
        else:
            grades[k] = grade_indicator(indicators.get(k, 0), good_high=True)

    score = sum(weights[k] * grades[k] for k in weights)
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
        "grades": grades,
        "weighted_credit_score": round(score, 2),
        "evaluation_score": evaluation_score,
        "risk_category": category,
        "credit_decision": decision,
    }


# ----------------------------------------------------------------------
#  GPT-5/4o reasoning engine with fallback and multilingual support
# ----------------------------------------------------------------------
def analyze_with_chatgpt(raw_text: str, indicators: dict, client: OpenAI = None):
    """
    Generates a structured financial credit evaluation report using GPT-5 or GPT-4o.
    Always outputs in English but detects and understands non-English input.
    """
    if client is None:
        client = get_openai_client()
    if not raw_text.strip():
        raw_text = "No extracted financial text available."

    results = compute_weighted_score(indicators)

    # ---------- prompt ----------
    prompt = f"""
You are a multilingual senior financial analyst generating a **Dynamic Credit Evaluation Report**.

If the source text is not in English, translate financial terminology internally
but output the final report in clear, professional English.

--- INPUT DATA ---
Financial document text (excerpt):
{raw_text[:2000]}

Extracted financial indicators:
{json.dumps(indicators, indent=2)}

Computed grades (A–E → 5–1):
{json.dumps(results['grades'], indent=2)}

Weighted Score: {results['weighted_credit_score']} / 5
Evaluation Score: {results['evaluation_score']} / 100
Risk Category: {results['risk_category']}
Credit Decision: {results['credit_decision']}

--- TASK ---
Write a concise institutional credit analysis with these sections:
1. Executive Summary
2. Quantitative Highlights
3. Strengths & Weaknesses
4. Scenario Stress Test
5. Strategic Outlook
6. Final Evaluation Summary

Use formal tone, clear structure, and avoid repetition.
    """

    # ---------- GPT Call with fallback ----------
    for model in ["gpt-5", "gpt-4o"]:
        try:
            completion = client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a professional institutional credit-risk analyst writing multilingual reports in English.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.4,
                max_tokens=1500,
            )

            text = completion.choices[0].message.content.strip()
            if text:
                return {
                    "analysis_raw": text,
                    "scores": results,
                    "structured_report": {
                        "company_name": "Auto-detected entity",
                        "analysis_timestamp": "auto",
                        "scores": results,
                        "summary": {"executive_overview": text[:400] + "..."},
                        "final_evaluation": results,
                    },
                }

        except Exception as e:
            print(f"⚠️ {model} failed: {e}")
            continue

    # ---------- Fallback if both models fail ----------
    print("❌ Both GPT-5 and GPT-4o calls failed.")
    return {
        "analysis_raw": "No analysis generated (API timeout or model unavailable).",
        "scores": results,
        "structured_report": {},
    }
