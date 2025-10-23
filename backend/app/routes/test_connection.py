import requests
from fastapi import APIRouter

router = APIRouter()

@router.get("/api/test-connection")
def test_connection():
    """
    Quick diagnostic route to confirm if Render can reach OpenAI.
    """
    try:
        r = requests.get("https://api.openai.com/v1/models", timeout=10)
        return {"status": "success", "response_code": r.status_code}
    except Exception as e:
        return {"error": str(e)}
