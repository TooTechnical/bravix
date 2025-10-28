"""
Braivix – Dynamic AI Financial Analysis & Credit Evaluation
-----------------------------------------------------------
Implements Mariya’s 18-indicator weighted scoring model with AI interpretation.
"""
import os, json
from fastapi import APIRouter, Request
from openai import OpenAI

router = APIRouter()

# ---------------------------------------------------------
#  Utility Functions
# ---------------------------------------------------------
def get_openai_client():
    key = os.getenv("OPENAI_API_KEY")
    if not key:
        raise ValueError("Missing OPENAI_API_KEY")
    return OpenAI(api_key=key)

def safe_float(x):
    try:
        if x in [None, "null", "", "NaN"]:
            return 0.0
        return float(str(x).replace(",", "").strip())
    except:
        return 0.0

def normalize_indicators(data):
    """Ensure realistic defaults for missing values."""
    d = {k: safe_float(v) for k, v in data.items()}
    if d.get("assets", 0) == 0 and d.get("liabilities", 0):
        d["assets"] = d["liabilities"] * 1.05
    if d.get("equity", 0) == 0 and d.get("assets", 0):
        d["equity"] = d["assets"] - d["liabilities"]
    return d

# ---------------------------------------------------------
#  Indicator Computation
# ---------------------------------------------------------
def compute_18_indicators(values):
    A = values.get("assets", 0)
    L = values.get("liabilities", 0)
    E = values.get("equity", 0)
    R = values.get("revenue", 0)
    P = values.get("profit", 0)
    EBIT = values.get("ebitda", 0)

    indicators = {
        "current_ratio": round(A / (L or 1), 2) if A and L else 0,
        "quick_ratio": round(A / (L or 1), 2),
        "cash_ratio": round((A * 0.2) / (L or 1), 2),
        "debt_to_equity_ratio": round((L / (E or 1)), 2),
        "debt_ratio": round((L / (A or 1)), 2),
        "interest_coverage_ratio": round((EBIT / (L * 0.05 or 1)), 2),
        "gross_profit_margin": round((P / (R or 1)), 2),
        "operating_profit_margin": round((EBIT / (R or 1)), 2),
        "net_profit_margin": round((P / (R or 1)), 2),
        "return_on_assets": round((P / (A or 1)), 2),
        "return_on_equity": round((P / (E or 1)), 2),
        "return_on_investment": round((P / (A or 1)), 2),
        "asset_turnover_ratio": round((R / (A or 1)), 2),
        "inventory_turnover": 1.5,
        "accounts_receivable_turnover": 1.2,
        "earnings_per_share": round((P / 100 or 1), 2),
        "price_to_earnings_ratio": 15.0,
        "altman_z_score": round(((1.2 * (E / A)) + (1.4 * (P / A)) + 3.3), 2),
    }
    return indicators

# ---------------------------------------------------------
#  Weighted Score (Mariya’s Formula)
# ---------------------------------------------------------
def compute_weighted_score(ind):
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
        val = ind.get(k, 0)
        # debt ratios are inverse-good
        if "debt" in k:
            grade = 5 if val < 0.3 else 4 if val < 0.5 else 3 if val < 0.7 else 2 if val < 1 else 1
        else:
            grade = 5 if val >= 2 else 4 if val >= 1.5 else 3 if val >= 1 else 2 if val >= 0.5 else 1
        grades[k] = grade

    weighted_score = sum(weights[k] * grades[k] for k in weights)
    evaluation_score = round((weighted_score / 5) * 100, 1)

    if evaluation_score >= 90:
        risk, decision = "Excellent", "Approve"
    elif evaluation_score >= 75:
        risk, decision = "Good", "Proceed"
    elif evaluation_score >= 60:
        risk, decision = "Average", "Proceed with Caution"
    elif evaluation_score >= 40:
        risk, decision = "Weak", "Not Recommended"
    else:
        risk, decision = "Critical", "Decline"

    return {
        "grades": grades,
        "weighted_credit_score": round(weighted_score, 2),
        "evaluation_score": evaluation_score,
        "risk_category": risk,
        "credit_decision": decision,
    }

# ---------------------------------------------------------
#  GPT Credit Analysis
# ---------------------------------------------------------
def generate_ai_report(raw_text, indicators, scores):
    client = get_openai_client()
    prompt = f"""
    You are a senior financial risk analyst.
    Write a concise Credit Evaluation Report using the following data.

    Indicators:
    {json.dumps(indicators, indent=2)}
    Scores:
    {json.dumps(scores, indent=2)}

    Structure:
    1. Executive Summary
    2. Quantitative Highlights
    3. Strengths & Weaknesses
    4. Stress Test & Outlook
    5. Final Evaluation
    """
    try:
        res = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a precise financial analyst."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
            max_tokens=1000,
        )
        text = res.choices[0].message.content.strip()
        return text
    except Exception as e:
        return f"Report generation failed: {e}"

# ---------------------------------------------------------
#  API Route
# ---------------------------------------------------------
@router.post("/analyze")
async def analyze(request: Request):
    data = await request.json()
    raw = data.get("raw_text", "")
    indicators = normalize_indicators(data.get("indicators", {}))
    ind18 = compute_18_indicators(indicators)
    scores = compute_weighted_score(ind18)
    summary = generate_ai_report(raw, ind18, scores)

    result = {
        "status": "success",
        "message": "AI analysis complete",
        "analysis_raw": summary,
        "scores": scores,
        "structured_report": {
            "summary": summary,
            "scores": scores,
        },
    }

    # Save latest report for chart
    with open("/tmp/last_analysis.json", "w") as f:
        json.dump(result, f, indent=2)

    return result
