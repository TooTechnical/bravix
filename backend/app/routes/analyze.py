"""
Bravix – AI Financial Analysis Route
------------------------------------
Handles incoming requests for AI-based financial report generation
using the GPT-5 and GPT-4o models.
"""

from fastapi import APIRouter, HTTPException, Request
from app.utils.analyze_with_chatgpt import analyze_with_chatgpt

router = APIRouter()


@router.post("/analyze")
async def analyze_file(request: Request):
    """
    Accepts parsed financial data and runs AI analysis.
    """
    try:
        data = await request.json()
        raw_text = data.get("raw_text", "")
        indicators = data.get("indicators", {})

        print("🧠 Received AI analysis request.")
        print(f"Raw text length: {len(raw_text)} | Indicators: {len(indicators)}")

        result = analyze_with_chatgpt(raw_text, indicators)
        print("✅ AI analysis completed successfully.")

        return {
            "status": "success",
            "message": "AI analysis complete",
            "ai_analysis": result.get("analysis_raw", "No response from AI"),
        }

    except Exception as e:
        print("❌ AI analysis failed:", str(e))
        raise HTTPException(status_code=500, detail=f"AI analysis failed: {str(e)}")
