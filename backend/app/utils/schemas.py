# schemas.py
from pydantic import BaseModel

class FinancialInput(BaseModel):
    revenue: float
    profit: float
    debt: float

class ScoreResponse(BaseModel):
    score: float
    insights: list
    input: FinancialInput
