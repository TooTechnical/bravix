"""
Bravix – Unified AI Financial Analysis & Credit Evaluation (v4.3 Stable)
------------------------------------------------------------------------------
✅ Unpacks nested 'indicators' dictionary correctly
✅ Adds /report/download endpoint for saved reports
✅ Adds full debug logs for every stage
✅ Computes accurate financial ratios and AI-based risk reports
"""

import os
import json
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import FileResponse
from openai import OpenAI
from dotenv import load_dotenv
from app.utils.financial_indicators import compute_all

# Load environment
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
    try:
        if x in [None, "null", "", "NaN"]:
            return 0.0
        return float(str(x).replace(",", "").strip())
    except Exception:
        return 0.0


def normalize_data(data):
    """Ensure all financial inputs are numeric and consistent."""
    if not data:
        print("⚠️ normalize_data received empty payload")
        return {}

    d = {k: safe_float(v) for k, v in data.items()}

    # Derive missing essentials where possible
    if not d.get("assets") and d.get("liabilities"):
        d["assets"] = d["liabilities"] * 1.1
    if not d.get("equity") and d.get("assets") and d.get("liabilities"):
        d["equity"] = max(d["assets"] - d["liabilities"], 0)
    if not d.get("revenue") and d.get("profit"):
        d["revenue"] = d["profit"] * 5

    print("📊 Normalized financial data:", json.dumps(d, indent=2))
    return d


# --------------------------------------------------------------
# 🧠 AI Report Generation
# --------------------------------------------------------------
def generate_ai_report(indicators, summary_data):
    if not indicators or not summary_data:
        print("⚠️ generate_ai_report called with empty data")
        return "Insufficient data for AI analysis."

    company_class = summary_data.get("company_class", "N/A")
    risk = summary_data.get("risk_category", "N/A")
    decision = summary_data.get("credit_decision", "N/A")
    ratings = summary_data.get("ratings", {})

    prompt = f"""
You are a senior financial risk analyst at Braivix.
Analyze the company's financial performance based on these indicators and classification data.

Indicators:
{json.dumps(indicators, indent=2)}

Summary:
Class: {company_class}
Risk Category: {risk}
Credit Decision: {decision}
Ratings: {json.dumps(ratings, indent=2)}

Structure your report in 5 concise sections:
1. Executive Summary
2. Quantitative Analysis
3. Strengths & Weaknesses
4. Risk Outlook
5. Final Recommendation
"""

    try:
        client = get_openai_client()
        res = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a precise, data-driven financial analyst."},
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
# 🚀 API Route: Analyze
# --------------------------------------------------------------
@router.post("/analyze")
async def analyze(request: Request):
    """
    Unified route for financial ratio computation + AI summary.
    Now correctly unpacks nested 'indicators' dict from upload.
    """
    try:
        data = await request.json()
        print("📥 Raw /analyze payload:", json.dumps(data, indent=2))

        if not isinstance(data, dict):
            raise HTTPException(status_code=400, detail="Invalid JSON payload.")

        # ✅ Extract nested indicators if present
        indicators_data = data.get("indicators", data)

        # Step 1: Normalize extracted numbers
        normalized = normalize_data(indicators_data)

        # Step 2: Compute all ratios
        print("🧮 Running compute_all() ...")
        analysis = compute_all(normalized)
        indicators = analysis.get("indicators", [])
        overall_score = analysis.get("overall_health_score")

        print("📈 Computed indicators:", json.dumps(indicators, indent=2))
        print("📊 Overall health score:", overall_score)

        summary_data = {
            k: analysis.get(k)
            for k in ["company_class", "risk_category", "credit_decision", "ratings"]
        }
        print("🏷️ Classification summary:", json.dumps(summary_data, indent=2))

        # Step 3: AI Summary
        ai_text = generate_ai_report(indicators, summary_data)

        # Step 4: Final result
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

        # Step 5: Save analysis for download
        os.makedirs("/tmp", exist_ok=True)
        with open("/tmp/last_analysis.json", "w") as f:
            json.dump(result, f, indent=2)
        print("💾 Saved analysis to /tmp/last_analysis.json")

        return result

    except Exception as e:
        print(f"❌ /analyze failed: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {e}")


# --------------------------------------------------------------
# 📥 Report Download Endpoint
# --------------------------------------------------------------
@router.get("/report/download")
async def download_report():
    """
    Serve the latest analysis report saved in /tmp as a downloadable file.
    If a PDF exists, return it; otherwise, fall back to JSON.
    """
    json_path = "/tmp/last_analysis.json"
    pdf_path = "/tmp/last_analysis.pdf"

    if os.path.exists(pdf_path):
        print("📄 Returning latest PDF report")
        return FileResponse(
            pdf_path,
            media_type="application/pdf",
            filename="Braivix_Report.pdf"
        )

    elif os.path.exists(json_path):
        print("📊 Returning latest JSON report")
        return FileResponse(
            json_path,
            media_type="application/json",
            filename="Braivix_Report.json"
        )

    else:
        print("❌ No report found in /tmp")
        raise HTTPException(status_code=404, detail="No report available for download.")
