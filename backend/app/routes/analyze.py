from fastapi import APIRouter, HTTPException, Header
from app.utils.analyzer import analyze_data

router = APIRouter()

@router.post("/analyze")
async def analyze_financials(payload: dict, x_api_key: str = Header(None)):
    """
    Accepts parsed financial data (from PDF, CSV, Excel, etc.)
    and uses GPT-5 + financial indicators to generate analysis.
    """
    try:
        # Perform the AI-driven analysis using helper function
        result = analyze_data(payload)

        # Return the structured AI analysis result
        return {
            "status": "success",
            "message": "Analysis complete",
            "result": result
        }

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid input data: {str(e)}"
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"AI analysis failed: {str(e)}"
        )
