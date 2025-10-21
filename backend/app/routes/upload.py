from fastapi import APIRouter, UploadFile, File, HTTPException
from app.utils.parsers import parse_file

router = APIRouter()

@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """
    Handles file uploads for the Bravix AI Financial Analyzer.
    Receives a PDF, CSV, Excel, or Word file and passes it to the parser.
    """
    try:
        # Parse the uploaded file (parse_file handles reading & format detection)
        parsed_data = parse_file(file)
        return parsed_data

    except ValueError as e:
        # For known parsing issues
        raise HTTPException(status_code=400, detail=f"Invalid file format: {str(e)}")

    except Exception as e:
        # For unexpected issues
        raise HTTPException(status_code=500, detail=f"File parsing failed: {str(e)}")
