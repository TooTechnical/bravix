import requests
from fastapi import APIRouter

router = APIRouter()

@router.get("/api/test-connection")
def test_connection():
    """
    Tests outbound HTTPS connectivity to OpenAI's API endpoint.
    This will help verify if Render can reach api.openai.com.
    """
    url = "https://api.openai.com/v1/models"
    try:
        response = requests.get(url, timeout=5)
        return {
            "status": "success",
            "response_code": response.status_code,
            "reachable": True,
            "note": "Outbound connection to OpenAI succeeded."
        }
    except requests.exceptions.Timeout:
        return {
            "status": "error",
            "reachable": False,
            "error": "Timeout — Render likely blocks external API calls."
        }
    except requests.exceptions.SSLError:
        return {
            "status": "error",
            "reachable": False,
            "error": "SSL verification failed — possible proxy or cert issue."
        }
    except requests.exceptions.ConnectionError as e:
        return {
            "status": "error",
            "reachable": False,
            "error": f"Connection error: {str(e)}"
        }
    except Exception as e:
        return {
            "status": "error",
            "reachable": False,
            "error": f"Unexpected error: {str(e)}"
        }
