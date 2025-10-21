from fastapi import APIRouter, HTTPException, Header
from app.utils.analyzer import analyze_data

router = APIRouter()

@router.post("/analyze")
async def analyze_financials(payload: dict, x_api_key: str = Header(None)):
    """
    Accepts parsed financial data (from PDF, CSV, Excel, or Word)
    and performs AI-driven financial analysis using GPT-5 and
    indicator computations to produce a summary report.
    """
    try:
        # Perform AI + financial analysis
        result = analyze_data(payload)

        # ✅ Extract analysis text safely
        if isinstance(result, dict):
            # If your analyzer returns a dict, try to find the AI summary text
            analysis_text = (
                result.get("analysis")
                or result.get("ai_output")
                or result.get("summary")
                or str(result)
            )
        else:
            analysis_text = str(result)

        # ✅ Return in structure expected by frontend
        return {
            "status": "success",
            "message": "AI analysis complete",
            "ai_analysis": analysis_text,  # frontend reads this field
        }

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid input data: {str(e)}",
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"AI analysis failed: {str(e)}",
        )
