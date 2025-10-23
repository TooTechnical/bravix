from fastapi import APIRouter, HTTPException, Header
from app.utils.analyzer import analyze_data
from app.utils.analyze_with_chatgpt import get_openai_client, analyze_with_chatgpt

router = APIRouter()

@router.post("/analyze")
async def analyze_financials(payload: dict, x_api_key: str = Header(None)):
    """
    Accepts parsed financial data (from PDF, CSV, Excel, or Word)
    and performs AI-driven financial analysis using GPT-5 and
    indicator computations to produce a summary report.
    """
    try:
        # 1️⃣ Perform financial computation & data parsing
        analysis_input = analyze_data(payload)

        # 2️⃣ Initialize OpenAI client *after* Render envs load
        client = get_openai_client()

        # 3️⃣ Run GPT-5/4o financial AI analysis
        ai_result = analyze_with_chatgpt(
            raw_text=str(analysis_input.get("raw_text", "")),
            indicators=analysis_input.get("indicators", {}),
            client=client
        )

        # 4️⃣ Extract readable text
        analysis_text = (
            ai_result.get("analysis_raw")
            if isinstance(ai_result, dict)
            else str(ai_result)
        )

        # ✅ Return clean response for frontend
        return {
            "status": "success",
            "message": "AI analysis complete",
            "ai_analysis": analysis_text,
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid input data: {str(e)}")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI analysis failed: {str(e)}")
