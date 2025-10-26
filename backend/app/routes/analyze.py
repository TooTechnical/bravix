"""
Bravix – AI Financial Analysis Route
------------------------------------
Handles incoming requests for AI-based financial report generation
using GPT-5 (primary) and GPT-4o (fallback) models.
"""

from fastapi import APIRouter, HTTPException, Request
from app.utils.analyze_with_chatgpt import analyze_with_chatgpt, get_openai_client

router = APIRouter()


@router.post("/analyze")
async def analyze_file(request: Request):
    """
    Accepts parsed financial data and performs AI-based financial risk analysis.
    Uses GPT-5/4o to evaluate indicators, compute weighted credit scores,
    and produce a full investor-grade financial report.
    """
    try:
        data = await request.json()
        raw_text = data.get("raw_text", "")
        indicators = data.get("indicators", {}) or {}

        print("🧠 Received AI analysis request.")
        print(f"📄 Raw text length: {len(raw_text)} | 📊 Indicators received: {len(indicators)}")

        # 🧮 Define Bravix grade normalization (used in scoring)
        grades = {
            "A": 5,
            "B": 4,
            "C": 3,
            "D": 2,
            "E": 1
        }

        # ✅ Initialize OpenAI client (singleton)
        client = get_openai_client()

        # ✅ Perform AI analysis (now includes `grades`)
        result = analyze_with_chatgpt(raw_text, indicators, grades, client=client)

        ai_text = result.get("analysis_raw", "")
        structured = result.get("structured_report", {})
        scores = result.get("scores", {})

        print(f"✅ AI analysis completed successfully. Output length: {len(ai_text)} characters")

        # ✅ Return JSON response for frontend integration
        return {
            "status": "success",
            "message": "AI analysis complete",
            "ai_analysis": ai_text,
            "structured_report": structured,
            "scores": scores,
            "model_used": "GPT-5 / 4o fallback",
        }

    except ValueError as ve:
        print(f"🚫 Configuration error: {ve}")
        raise HTTPException(status_code=500, detail=str(ve))

    except Exception as e:
        print(f"❌ AI analysis failed: {e}")
        raise HTTPException(status_code=500, detail=f"AI analysis failed: {e}")
