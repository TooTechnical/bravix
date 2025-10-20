from fastapi import APIRouter, UploadFile, File, HTTPException
from app.utils.parsers import parse_file

router = APIRouter()

@router.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    try:
        # Pass the UploadFile object directly — parser handles reading
        parsed = parse_file(file)
        return parsed
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"File parsing failed: {str(e)}")
