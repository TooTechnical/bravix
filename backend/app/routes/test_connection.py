from fastapi import APIRouter
import requests

router = APIRouter()

@router.get("/test-connection")
def test_connection():
    """
    Connectivity test to confirm backend is working.
    """
    try:
        r = requests.get("https://api.openai.com/v1/models", timeout=10)
        return {"status": "success", "response_code": r.status_code, "reachable": True}
    except Exception as e:
        return {"error": str(e), "reachable": False}
