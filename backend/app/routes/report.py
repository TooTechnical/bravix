import os, json
from fastapi import APIRouter

router = APIRouter()

@router.get("/report")
def get_latest_report():
    path = "/tmp/last_analysis.json"
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return {"status": "error", "message": "No report available yet"}
