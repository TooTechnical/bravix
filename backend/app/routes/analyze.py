"""
Braivix – AI Financial Analysis & Credit Evaluation (Context-Aware)
-------------------------------------------------------------------
Performs full credit scoring and GPT-5 reasoning with contextual awareness
of the company's parsed data, name, year, and summary.
"""

import os
import json
from fastapi import APIRouter, HTTPException, Request
from openai import OpenAI

router = APIRouter()


# ----------------------------------------------------------------------
#  OpenAI client setup
# ----------------------------------------------------------------------
def get_openai_client():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("Missing OPENAI_API_KEY environment variable")
    return OpenAI(api_key=api_key)


# ----------------------------------------------------------------------
#  Grade calculator
# ----------------------------------------------------------------------
def grade_indicator(value, good_high=True):
    """Assign grades (A–E → 5–1) depending on whether a higher value is better."""
    try:
        v = float(value)
        if good_high:
            if v >= 2: return 5
            elif v >= 1.5: return 4
            elif v >= 1.0: return 3
            elif v >= 0.5: return 2
            else: return 1
        else:  # For ratios where lower is better
            if v <= 0.3: return 5
            elif v <= 0.5: return 4
            elif v <= 0.7: return 3
            elif v <= 1.0: return 2
            else: return 1
    except Exception:
        return 3


# ----------------------------------------------------------------------
#  Weighted credit score computation
# ----------------------------------------------------------------------
def compute_weighted_score(indicators: dict):
    """Derive grades dynamically from indicators and compute Σ(wᵢ×sᵢ)."""
    weights = {
        "current_ratio": 0.08, "quick_ratio": 0.08, "cash_ratio": 0.08,
        "debt_to_equity_ratio": 0.10, "debt_ratio": 0.10, "interest_coverage_ratio": 0.10,
        "gross_profit_margin": 0.05, "operating_profit_margin": 0.05, "net_profit_margin": 0.05,
        "return_on_assets": 0.05, "return_on_equity": 0.05, "return_on_investment": 0.05,
        "asset_turnover_ratio": 0.05, "inventory_turnover": 0.05, "accounts_receivable_turnover": 0.05,
        "earnings_per_share": 0.025, "price_to_earnings_ratio": 0.025, "altman_z_score": 0.06
    }

    grades = {}
    for k, w in weights.items():
        good_high = not ("debt" in k or "ratio" in k)
        grades[k] = grade_indicator(indicators.get(k, 0), good_high=good_high)

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
        "credit_decision": decision
    }


# ----------------------------------------------------------------------
#  GPT-based financial analysis
# ----------------------------------------------------------------------
def analyze_with_chatgpt(raw_text: str, indicators: dict, summary: str = "", client=None):
    """Run GPT-5 contextual financial reasoning."""
    if client is None:
        client = get_openai_client()
    if not raw_text.strip():
        raw_text = "No extracted financial text available."

    results = compute_weighted_score(indicators)

    company_name = indicators.get("company_name", "Unknown Entity")
    fiscal_year = indicators.get("fiscal_year", "Current Period")

    # ---------------- Prompt ----------------
    prompt = f"""
You are a **senior institutional credit-risk analyst** generating a comprehensive
AI-based report for **{company_name}**, fiscal year **{fiscal_year}**.

--- Context Summary ---
{summary}

--- Extracted Financial Indicators ---
{json.dumps(indicators, indent=2)}

--- Weighted Score Computation ---
Score = Σ(wᵢ×sᵢ) = {results['weighted_credit_score']} / 5  
Evaluation Score = {results['evaluation_score']} / 100  
Risk Category = {results['risk_category']}  
Decision = {results['credit_decision']}

--- TASK ---
Generate a concise, data-driven institutional-grade report with these sections:

1. Executive Summary
2. Quantitative Highlights (financial metrics table)
3. Key Strengths & Weaknesses
4. Scenario Stress Test
5. Strategic Outlook
6. Final Credit Evaluation Summary

Your tone: professional, analytical, and factual. Avoid generic phrasing.
Focus on what the extracted data implies for risk and creditworthiness.
    """

    try:
        completion = client.chat.completions.create(
            model="gpt-5",
            messages=[
                {"role": "system", "content": "You are an expert financial risk analyst creating credit assessment reports."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.4,
            max_tokens=1800,
        )

        text = completion.choices[0].message.content.strip()

        return {
            "analysis_raw": text,
            "scores": results,
            "structured_report": {
                "company_name": company_name,
                "fiscal_year": fiscal_year,
                "summary": summary,
                "scores": results,
            },
            "model_used": "GPT-5 / 4o fallback"
        }

    except Exception as e:
        print("❌ AI analysis failed:", e)
        return {
            "analysis_raw": "No analysis generated.",
            "scores": results,
            "structured_report": {},
        }


# ----------------------------------------------------------------------
#  API Endpoint
# ----------------------------------------------------------------------
@router.post("/analyze")
async def analyze_file(request: Request):
    """
    Accepts parsed financial data (from /upload) and performs AI-based financial risk analysis.
    """
    try:
        data = await request.json()
        raw_text = data.get("raw_text", "")
        indicators = data.get("indicators", {}) or {}
        summary = data.get("summary", "")

        print("🧠 Received AI analysis request for:", indicators.get("company_name", "Unknown"))

        client = get_openai_client()
        result = analyze_with_chatgpt(raw_text, indicators, summary, client=client)

        print(f"✅ AI analysis complete for {indicators.get('company_name', 'Entity')} "
              f"({result['scores']['evaluation_score']}/100 – {result['scores']['risk_category']})")

        return {
            "status": "success",
            "message": "AI analysis complete",
            **result,
        }

    except ValueError as ve:
        raise HTTPException(status_code=500, detail=str(ve))
    except Exception as e:
        print(f"❌ Analysis route failed: {e}")
        raise HTTPException(status_code=500, detail=f"AI analysis failed: {e}")
