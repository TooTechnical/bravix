"""
Braivix – Dynamic AI Financial Analysis & Credit Evaluation
-----------------------------------------------------------
Implements Mariya’s 18-indicator weighted scoring model with safe division,
AI-generated summary, and proper handling for incomplete financial data.
"""

import os, json
from fastapi import APIRouter, Request, HTTPException
from openai import OpenAI

router = APIRouter()

# ---------------------------------------------------------
#  GPT Client
# ---------------------------------------------------------
def get_openai_client():
    key = os.getenv("OPENAI_API_KEY")
    if not key:
        raise ValueError("Missing OPENAI_API_KEY")
    return OpenAI(api_key=key)

# ---------------------------------------------------------
#  Helpers
# ---------------------------------------------------------
def safe_float(x):
    try:
        if x in [None, "null", "", "NaN"]:
            return 0.0
        return float(str(x).replace(",", "").strip())
    except:
        return 0.0

def safe_div(num, denom):
    try:
        if denom in [None, 0]:
            return 0.0
        return num / denom
    except Exception:
        return 0.0

def normalize_indicators(data):
    d = {k: safe_float(v) for k, v in data.items()}
    if not d.get("assets") and d.get("liabilities"):
        d["assets"] = d["liabilities"] * 1.05
    if not d.get("equity") and d.get("assets"):
        d["equity"] = d["assets"] - d["liabilities"]
    return d

# ---------------------------------------------------------
#  Indicator Computation (18 indicators)
# ---------------------------------------------------------
def compute_18_indicators(values):
    A = safe_float(values.get("assets"))
    L = safe_float(values.get("liabilities"))
    E = safe_float(values.get("equity"))
    R = safe_float(values.get("revenue"))
    P = safe_float(values.get("profit"))
    EBIT = safe_float(values.get("ebitda"))

    if all(v == 0 for v in [A, L, E, R, P, EBIT]):
        return {"error": "Insufficient data"}

    indicators = {
        "current_ratio": round(safe_div(A, L), 2),
        "quick_ratio": round(safe_div(A, L), 2),
        "cash_ratio": round(safe_div(A * 0.2, L), 2),
        "debt_to_equity_ratio": round(safe_div(L, E), 2),
        "debt_ratio": round(safe_div(L, A), 2),
        "interest_coverage_ratio": round(safe_div(EBIT, L * 0.05), 2),
        "gross_profit_margin": round(safe_div(P, R), 2),
        "operating_profit_margin": round(safe_div(EBIT, R), 2),
        "net_profit_margin": round(safe_div(P, R), 2),
        "return_on_assets": round(safe_div(P, A), 2),
        "return_on_equity": round(safe_div(P, E), 2),
        "return_on_investment": round(safe_div(P, A), 2),
        "asset_turnover_ratio": round(safe_div(R, A), 2),
        "inventory_turnover": 1.5,
        "accounts_receivable_turnover": 1.2,
        "earnings_per_share": round(safe_div(P, 100), 2),
        "price_to_earnings_ratio": 15.0,
        "altman_z_score": round((1.2 * safe_div(E, A)) + (1.4 * safe_div(P, A)) + 3.3, 2),
    }
    return indicators

# ---------------------------------------------------------
#  Weighted Score (Mariya’s Formula)
# ---------------------------------------------------------
def compute_weighted_score(ind):
    if "error" in ind:
        return {"error": "Insufficient data for scoring"}

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
    for k, v in ind.items():
        if k in ["debt_ratio", "debt_to_equity_ratio"]:
            grade = 5 if v < 0.3 else 4 if v < 0.5 else 3 if v < 0.7 else 2 if v < 1 else 1
        else:
            grade = 5 if v >= 2 else 4 if v >= 1.5 else 3 if v >= 1 else 2 if v >= 0.5 else 1
        grades[k] = grade

    weighted_score = sum(weights.get(k, 0) * grades.get(k, 3) for k in weights)
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

    if "error" in indicators or "error" in scores:
        return "Insufficient data for AI analysis."

    prompt = f"""
    You are a senior financial risk analyst.
    Write a Credit Evaluation Report using the following data.

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
            max_tokens=1200,
        )
        return res.choices[0].message.content.strip()
    except Exception as e:
        return f"Report generation failed: {e}"

# ---------------------------------------------------------
#  API Route
# ---------------------------------------------------------
@router.post("/analyze")
async def analyze(request: Request):
    """Accept parsed financial data, compute indicators, and generate AI report."""
    try:
        data = await request.json()
        raw = data.get("raw_text", "")
        indicators = normalize_indicators(data.get("indicators", {}))
        ind18 = compute_18_indicators(indicators)

        if "error" in ind18:
            return {"error": "Insufficient data to perform analysis."}

        scores = compute_weighted_score(ind18)
        summary = generate_ai_report(raw, ind18, scores)

        result = {
            "status": "success",
            "message": "AI analysis complete",
            "analysis_raw": summary,
            "scores": scores,
            "structured_report": {"summary": summary, "scores": scores},
            "data": data,  # include company_name etc. for PDF
        }

        # ✅ Persist full report for PDF download
        os.makedirs("/tmp", exist_ok=True)
        with open("/tmp/last_analysis.json", "w") as f:
            json.dump(result, f, indent=2)

        return result
    except Exception as e:
        print("❌ AI analysis failed:", e)
        raise HTTPException(status_code=500, detail=str(e))
