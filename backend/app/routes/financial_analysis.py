from fastapi import APIRouter, HTTPException, Header
from app.financial_indicators import compute_all

router = APIRouter()

@router.post("/financial-analysis")
async def financial_analysis(financial_data: dict, x_api_key: str = Header(None)):
    """
    Handles computation of all 18 key financial indicators.
    Receives parsed financial data from the frontend or upload parser.
    """
    try:
        results = compute_all(financial_data)
        return {
            "status": "success",
            "message": "Financial indicators calculated successfully",
            "indicators": results,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Financial analysis failed: {str(e)}")
