from fastapi import APIRouter, HTTPException
from app.routes.indicators import calculate_indicators
from app.utils.analyze_with_chatgpt import analyze_with_chatgpt
import traceback

router = APIRouter()

@router.post("/analyze")
async def analyze_financials(payload: dict):
    """
    Accepts parsed financial data (from CSV, PDF, Excel, etc.),
    calculates indicators, and asks GPT-5 for analysis.
    """
    try:
        # ✅ Validate
        if not payload:
            raise HTTPException(status_code=400, detail="Missing financial data payload")

        # ✅ Calculate indicators
        try:
            indicators = calculate_indicators(payload)
        except Exception as calc_err:
            print("⚠️ Error calculating indicators:")
            traceback.print_exc()
            raise HTTPException(status_code=400, detail=f"Indicator calculation failed: {calc_err}")

        # ✅ Prepare summary for GPT-5
        text_summary = (
            f"Revenue: {payload.get('revenue')} | "
            f"Profit: {payload.get('profit')} | "
            f"Debt: {payload.get('debt')} | "
            f"Assets: {payload.get('assets')} | "
            f"Equity: {payload.get('equity')} | "
            f"Indicators: {indicators}"
        )

        print("🧠 Sending this summary to GPT-5:")
        print(text_summary[:500])
        print("------------------------------------------------------------")

        # ✅ Call GPT-5
        ai_analysis = analyze_with_chatgpt(text_summary, indicators)

        # ✅ Return combined result
        return {
            "status": "success",
            "financial_indicators": indicators,
            "ai_analysis": ai_analysis,
        }

    except HTTPException:
        raise
    except Exception as e:
        print("🔥 Unhandled exception in /api/analyze:")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
