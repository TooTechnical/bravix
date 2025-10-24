import os
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends, Header
from pydantic import BaseModel
from app.utils.analyze_with_chatgpt import analyze_with_chatgpt
from dotenv import load_dotenv

router = APIRouter()

load_dotenv()

API_KEY = "BRAVIX-DEMO-SECURE-KEY-2025"


# ✅ Security dependency
async def verify_api_key(x_api_key: str = Header(None)):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid or missing API Key")


class AnalysisRequest(BaseModel):
    text: str
    indicators: dict


@router.post("/api/analyze", dependencies=[Depends(verify_api_key)])
async def analyze(request: AnalysisRequest):
    """
    Main AI Analysis endpoint.
    Accepts extracted text and financial indicators,
    sends them to GPT for analysis, and returns the AI’s report.
    """
    try:
        print("🧠 Sending indicators + text to GPT analysis...")
        ai_analysis = analyze_with_chatgpt(
            raw_text=request.text,
            indicators=request.indicators
        )
        return {
            "status": "success",
            "message": "AI analysis complete",
            "ai_analysis": ai_analysis.get("analysis_raw")
        }

    except Exception as e:
        print("❌ AI analysis failed:", e)
        raise HTTPException(status_code=500, detail=f"AI analysis failed: {str(e)}")
