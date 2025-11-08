"""
Bravix – Unified AI Financial Analysis & Credit Evaluation (v4.0)
-----------------------------------------------------------------
Integrates precise ratio calculations from financial_indicators.py
and generates AI-based credit reports aligned with Mariya’s model.
"""

import os
import json
from fastapi import APIRouter, Request, HTTPException
from openai import OpenAI
from dotenv import load_dotenv
from app.utils.financial_indicators import compute_all  # ✅ Use the new accurate engine

# Load environment variables early
load_dotenv()

router = APIRouter()

# --------------------------------------------------------------
# 🔐 Helper functions
# --------------------------------------------------------------
def get_openai_client():
    key = os.getenv("OPENAI_API_KEY")
    if not key:
        print("❌ Missing OPENAI_API_KEY in environment!")
        raise ValueError("Missing OPENAI_API_KEY")

    print("🔑 OpenAI key loaded successfully (first 8 chars):", key[:8] + "...")
    return OpenAI(api_key=key)


def safe_float(x):
    """Convert safely to float."""
    try:
        if x in [None, "null", "", "NaN"]:
            return 0.0
        return float(str(x).replace(",", "").strip())
    except Exception:
        return 0.0


def normalize_data(data):
    """Ensure all financial inputs are numeric and consistent."""
    if not data:
        return {}
    d = {k: safe_float(v) for k, v in data.items()}

    # Derive common missing fields
    if not d.get("assets") and d.get("liabilities"):
        d["assets"] = d["liabilities"] * 1.1
    if not d.get("equity") and d.get("assets") and d.get("liabilities"):
        d["equity"] = max(d["assets"] - d["liabilities"], 0)
    if not d.get("revenue") and d.get("profit"):
        d["revenue"] = d["profit"] * 5
    return d


# --------------------------------------------------------------
# 🧠 AI Report Generation
# --------------------------------------------------------------
def generate_ai_report(indicators, summary_data):
    """Generate professional credit evaluation report using OpenAI."""
    if not indicators or not summary_data:
        return "Insufficient data for AI analysis."

    company_class = summary_data.get("company_class", "N/A")
    risk = summary_data.get("risk_category", "N/A")
    decision = summary_data.get("credit_decision", "N/A")
    ratings = summary_data.get("ratings", {})

    prompt = f"""
You are a senior financial risk analyst at Braivix.
Analyze the company's financial performance based on these 18 key indicators and classification data.

Indicators:
{json.dumps(indicators, indent=2)}

Overall Summary:
Class: {company_class}
Risk Category: {risk}
Credit Decision: {decision}
Ratings: {json.dumps(ratings, indent=2)}

Structure your report in 5 sections:
1. Executive Summary (explain what the class/risk means)
2. Quantitative Analysis (highlight key ratios driving the score)
3. Strengths & Weaknesses (data-based, concise)
4. Risk Outlook (describe stability, leverage, and liquidity)
5. Final Recommendation (short, clear, investor-style summary)
"""

    try:
        client = get_openai_client()
        res = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a precise, data-driven financial analyst. Be concise and professional."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.25,
            max_tokens=1200,
        )
        return res.choices[0].message.content.strip()
    except Exception as e:
        print(f"❌ OpenAI API error: {e}")
        return f"Report generation failed: {e}"


# --------------------------------------------------------------
# 🚀 API Route
# --------------------------------------------------------------
@router.post("/analyze")
async def analyze(request: Request):
    """
    Main endpoint for financial + AI analysis.
    Uses accurate financial indicator engine and generates
    AI-based summary with classification and credit rating.
    """
    try:
        data = await request.json()
        if not isinstance(data, dict):
            raise HTTPException(status_code=400, detail="Invalid JSON payload.")

        # Step 1: Normalize incoming numbers
        normalized = normalize_data(data)

        # Step 2: Compute ratios + classification
        analysis = compute_all(normalized)
        indicators = analysis.get("indicators", [])
        overall_score = analysis.get("overall_health_score")
        summary_data = {
            k: analysis.get(k)
            for k in ["company_class", "risk_category", "credit_decision", "ratings"]
        }

        # Step 3: AI Summary
        ai_text = generate_ai_report(indicators, summary_data)

        # Step 4: Combine into final result
        result = {
            "status": "success",
            "message": "AI financial analysis completed successfully.",
            "indicators": indicators,
            "overall_health_score": overall_score,
            "classification": summary_data,
            "ai_report": ai_text,
            "structured_report": {
                "summary": ai_text,
                "scores": {
                    "evaluation_score": overall_score,
                    **summary_data,
                },
            },
        }

        # Save latest report to /tmp for PDF download
        os.makedirs("/tmp", exist_ok=True)
        with open("/tmp/last_analysis.json", "w") as f:
            json.dump(result, f, indent=2)

        return result

    except Exception as e:
        print(f"❌ /analyze failed: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {e}")
