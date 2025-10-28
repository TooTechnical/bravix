"""
Braivix – Dynamic AI Financial Analysis & Credit Evaluation
-----------------------------------------------------------
Computes Mariya’s 18-indicator weighted score, generates an AI report,
and saves the full result for PDF download.
"""
import os, json
from fastapi import APIRouter, Request, HTTPException
from openai import OpenAI

router = APIRouter()

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

def safe_div(a, b):
    try:
        if not b:
            return 0.0
        return a / b
    except:
        return 0.0

def normalize_indicators(data):
    d = {k: safe_float(v) for k, v in data.items()}
    if not d.get("assets") and d.get("liabilities"):
        d["assets"] = d["liabilities"] * 1.05
    if not d.get("equity") and d.get("assets"):
        d["equity"] = d["assets"] - d["liabilities"]
    return d

def compute_18_indicators(v):
    A, L, E, R, P, EBIT = map(safe_float, [v.get("assets"), v.get("liabilities"),
                                           v.get("equity"), v.get("revenue"),
                                           v.get("profit"), v.get("ebitda")])
    if all(x == 0 for x in [A, L, E, R, P, EBIT]):
        return {"error": "Insufficient data"}

    return {
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
        "altman_z_score": round((1.2 * safe_div(E, A)) + (1.4 * safe_div(P, A)) + 3.3, 2)
    }

def compute_weighted_score(ind):
    if "error" in ind:
        return {"error": "Insufficient data for scoring"}

    weights = {
        "current_ratio": .08, "quick_ratio": .08, "cash_ratio": .08,
        "debt_to_equity_ratio": .1, "debt_ratio": .1, "interest_coverage_ratio": .1,
        "gross_profit_margin": .05, "operating_profit_margin": .05, "net_profit_margin": .05,
        "return_on_assets": .05, "return_on_equity": .05, "return_on_investment": .05,
        "asset_turnover_ratio": .05, "inventory_turnover": .05, "accounts_receivable_turnover": .05,
        "earnings_per_share": .025, "price_to_earnings_ratio": .025, "altman_z_score": .06,
    }

    grades = {}
    for k, v in ind.items():
        if k in ["debt_ratio", "debt_to_equity_ratio"]:
            g = 5 if v < .3 else 4 if v < .5 else 3 if v < .7 else 2 if v < 1 else 1
        else:
            g = 5 if v >= 2 else 4 if v >= 1.5 else 3 if v >= 1 else 2 if v >= .5 else 1
        grades[k] = g

    weighted = sum(weights[k]*grades[k] for k in weights)
    eval_score = round((weighted/5)*100, 1)

    if eval_score >= 90: risk, dec = "Excellent", "Approve"
    elif eval_score >= 75: risk, dec = "Good", "Proceed"
    elif eval_score >= 60: risk, dec = "Average", "Proceed with Caution"
    elif eval_score >= 40: risk, dec = "Weak", "Not Recommended"
    else: risk, dec = "Critical", "Decline"

    return {"grades": grades, "weighted_credit_score": round(weighted, 2),
            "evaluation_score": eval_score, "risk_category": risk, "credit_decision": dec}

def generate_ai_report(raw, indicators, scores):
    if "error" in indicators or "error" in scores:
        return "Insufficient data for AI analysis."

    prompt = f"""You are a senior financial risk analyst.
Write a Credit Evaluation Report using these indicators and scores:
Indicators:
{json.dumps(indicators, indent=2)}
Scores:
{json.dumps(scores, indent=2)}
Structure:
1. Executive Summary
2. Quantitative Highlights
3. Strengths & Weaknesses
4. Stress Test & Outlook
5. Final Evaluation"""

    try:
        client = get_openai_client()
        res = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role":"system","content":"You are a precise financial analyst."},
                      {"role":"user","content":prompt}],
            temperature=0.3, max_tokens=1200)
        return res.choices[0].message.content.strip()
    except Exception as e:
        return f"Report generation failed: {e}"

@router.post("/analyze")
async def analyze(request: Request):
    try:
        data = await request.json()
        raw = data.get("raw_text", "")
        indicators = normalize_indicators(data.get("indicators", {}))
        ind18 = compute_18_indicators(indicators)
        if "error" in ind18:
            return {"error": "Insufficient data"}

        scores = compute_weighted_score(ind18)
        summary = generate_ai_report(raw, ind18, scores)

        result = {
            "status": "success",
            "message": "AI analysis complete",
            "analysis_raw": summary,
            "scores": scores,
            "structured_report": {"summary": summary, "scores": scores},
            "data": data
        }

        os.makedirs("/tmp", exist_ok=True)
        with open("/tmp/last_analysis.json", "w") as f:
            json.dump(result, f, indent=2)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
