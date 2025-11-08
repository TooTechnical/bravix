"""
Bravix – Financial Analysis Endpoint (v3.0)
--------------------------------------------
Handles computation of all 18 financial indicators from provided data.
Ensures safe math handling, structured response, and validation.
"""

from fastapi import APIRouter, HTTPException, Header, Request
from app.utils.financial_indicators import compute_all

router = APIRouter()

@router.post("/financial-analysis")
async def financial_analysis(request: Request, x_api_key: str = Header(None)):
    """
    Handles computation of all 18 key financial indicators.
    Receives parsed or manually entered financial data from frontend.
    Returns normalized results and indicator categories.
    """
    try:
        financial_data = await request.json()

        if not financial_data or not isinstance(financial_data, dict):
            raise HTTPException(status_code=400, detail="Invalid or missing financial data payload.")

        results = compute_all(financial_data)

        if not results or "indicators" not in results:
            raise HTTPException(status_code=422, detail="Indicator computation returned empty results.")

        return {
            "status": "success",
            "message": "Financial indicators calculated successfully.",
            "data_received": financial_data,
            "results": results,
            "categories": {
                "Liquidity Ratios": [
                    "current_ratio", "quick_ratio", "cash_ratio"
                ],
                "Leverage Ratios": [
                    "debt_to_equity_ratio", "debt_ratio", "interest_coverage_ratio"
                ],
                "Profitability Ratios": [
                    "gross_profit_margin", "operating_profit_margin", "net_profit_margin",
                    "return_on_assets", "return_on_equity", "return_on_investment"
                ],
                "Efficiency Ratios": [
                    "asset_turnover_ratio", "inventory_turnover", "accounts_receivable_turnover"
                ],
                "Valuation & Solvency": [
                    "earnings_per_share", "price_to_earnings_ratio", "altman_z_score"
                ],
            },
        }

    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Financial analysis failed: {str(e)}")
