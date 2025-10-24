import os
import requests
from fastapi import APIRouter

router = APIRouter()

@router.get("/api/test-connection")
def test_connection():
    """
    Simple endpoint to verify that the server can reach OpenAI
    and that your API key works correctly.
    """
    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        return {"status": "error", "message": "OPENAI_API_KEY is missing in environment variables."}

    headers = {"Authorization": f"Bearer {api_key}"}
    try:
        # Make a simple GET call to OpenAI’s model list endpoint
        r = requests.get("https://api.openai.com/v1/models", headers=headers, timeout=10)
        reachable = r.status_code == 200
        return {
            "status": "success",
            "response_code": r.status_code,
            "reachable": reachable,
            "note": "Outbound connection to OpenAI succeeded." if reachable else "Connection failed."
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "reachable": False
        }
