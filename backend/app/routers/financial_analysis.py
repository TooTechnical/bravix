from fastapi import APIRouter
from app.financial_indicators import compute_all

router = APIRouter()

@router.post("/api/financial-analysis")
async def financial_analysis(financial_data: dict):
    return compute_all(financial_data)
