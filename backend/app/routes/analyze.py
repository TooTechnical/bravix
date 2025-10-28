"""
Braivix – Dynamic AI Financial Analysis & Credit Evaluation
-----------------------------------------------------------
Integrates extracted financial figures from the upload route,
computes ratios dynamically, and generates a GPT-5 credit report.
"""
import os, json
from fastapi import APIRouter, Request, HTTPException
from openai import OpenAI

router = APIRouter()

# ----------------------------------------------------------------------
#  GPT client setup
# ----------------------------------------------------------------------
def get_openai_client():
    key = os.getenv("OPENAI_API_KEY")
    if not key:
        raise ValueError("Missing OPENAI_API_KEY")
    return OpenAI(api_key=key)

# ----------------------------------------------------------------------
#  Weighted score + ratio computation
# ----------------------------------------------------------------------
def compute_indicators_from_basics(data: dict):
    """Build ratio dictionary from AI-extracted values."""
    rev = data.get("revenue") or 0
    prof = data.get("profit") or 0
    eq = data.get("equity") or 0
    asst = data.get("assets") or 0
    liab = data.get("liabilities") or 0
    ebitda = data.get("ebitda") or 0

    out = {}
    try:
        if rev: out["net_profit_margin"] = round((prof / rev) * 100, 2)
        if asst: out["return_on_assets"] = round((prof / asst) * 100, 2)
        if eq: out["return_on_equity"] = round((prof / eq) * 100, 2)
        if asst and eq:
            out["debt_ratio"] = round((asst - eq) / asst, 3)
            out["debt_to_equity_ratio"] = round((asst - eq) / eq, 3)
        if rev and ebitda: out["operating_profit_margin"] = round((ebitda / rev) * 100, 2)
    except Exception:
        pass

    out.update({
        "assets": asst, "liabilities": liab, "equity": eq,
        "revenue": rev, "profit": prof, "ebitda": ebitda
    })
    return out

def grade_indicator(value, good_high=True):
    try:
        v = float(value)
        if good_high:
            if v >= 2: return 5
            elif v >= 1.5: return 4
            elif v >= 1.0: return 3
            elif v >= 0.5: return 2
            else: return 1
        else:
            if v <= 0.3: return 5
            elif v <= 0.5: return 4
            elif v <= 0.7: return 3
            elif v <= 1.0: return 2
            else: return 1
    except:
        return 3

def compute_weighted_score(indicators: dict):
    weights = {
        "current_ratio": 0.08, "quick_ratio": 0.08, "cash_ratio": 0.08,
        "debt_to_equity_ratio": 0.10, "debt_ratio": 0.10,
        "interest_coverage_ratio": 0.10,
        "gross_profit_margin": 0.05, "operating_profit_margin": 0.05,
        "net_profit_margin": 0.05, "return_on_assets": 0.05,
        "return_on_equity": 0.05, "return_on_investment": 0.05,
        "asset_turnover_ratio": 0.05, "inventory_turnover": 0.05,
        "accounts_receivable_turnover": 0.05,
        "earnings_per_share": 0.025, "price_to_earnings_ratio": 0.025,
        "altman_z_score": 0.06
    }
    grades = {}
    for k, w in weights.items():
        if "debt" in k: grades[k] = grade_indicator(indicators.get(k, 0), good_high=False)
        else: grades[k] = grade_indicator(indicators.get(k, 0), good_high=True)
    score = sum(weights[k]*grades[k] for k in weights)
    eval_score = round((score/5)*100,1)
    if eval_score>=90: cat,dec="Excellent","Safe to Proceed"
    elif eval_score>=76: cat,dec="Good","Safe to Proceed"
    elif eval_score>=60: cat,dec="Average","Proceed with Caution"
    elif eval_score>=40: cat,dec="Weak","Not Recommended"
    else: cat,dec="Critical","Decline"
    return {"grades":grades,"weighted_credit_score":round(score,2),
            "evaluation_score":eval_score,"risk_category":cat,"credit_decision":dec}

# ----------------------------------------------------------------------
#  GPT-5 reasoning
# ----------------------------------------------------------------------
def analyze_with_chatgpt(raw_text:str, indicators:dict, client=None):
    if client is None: client=get_openai_client()
    base = compute_indicators_from_basics(indicators)
    results = compute_weighted_score(base)
    prompt=f"""
You are a senior financial analyst generating a concise Credit Evaluation Report.

--- DATA ---
{json.dumps(base,indent=2)}

--- SCORES ---
{json.dumps(results,indent=2)}

--- TASK ---
Write a 5-section professional report:
1. Executive Summary
2. Quantitative Highlights
3. Strengths & Weaknesses
4. Stress Test & Outlook
5. Final Evaluation
"""
    try:
        comp=client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role":"system","content":"You are a professional financial analyst."},
                {"role":"user","content":prompt}],
            temperature=0.4,
            max_tokens=1000)
        text=comp.choices[0].message.content.strip()
        return {"analysis_raw":text,"scores":results,"structured_report":{"summary":text,"scores":results}}
    except Exception as e:
        print("❌ analysis failed:",e)
        return {"analysis_raw":"No analysis generated.","scores":results,"structured_report":{}}

# ----------------------------------------------------------------------
#  FastAPI Route
# ----------------------------------------------------------------------
@router.post("/analyze")
async def analyze_file(request: Request):
    """
    Accepts parsed data (from upload route) and generates GPT-5 analysis.
    """
    try:
        data = await request.json()
        raw_text = data.get("raw_text", "")
        indicators = data.get("indicators", {}) or {}

        print("🧠 Analyzing financial data via GPT...")
        result = analyze_with_chatgpt(raw_text, indicators)

        return {
            "status": "success",
            "message": "AI analysis complete",
            "analysis_raw": result.get("analysis_raw"),
            "scores": result.get("scores"),
            "structured_report": result.get("structured_report"),
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI analysis failed: {e}")
